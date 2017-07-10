#!/usr/bin/env python

# '''
# Copyright (c) 2015, Mark Silliman
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# '''

# BrainBot

import rospy
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import actionlib
from actionlib_msgs.msg import *
from geometry_msgs.msg import Pose, PoseWithCovarianceStamped, Point, Quaternion, Twist
from tf.transformations import quaternion_from_euler
import json
import urllib2
import time  # for sleep()
import roslib
from kobuki_msgs.msg import PowerSystemEvent, AutoDockingAction, AutoDockingGoal, \
    SensorState  # for kobuki base power and auto docking
from kobuki_msgs.msg import ButtonEvent  # for kobuki base's b0 button
import math  # for comparing if Kobuki's power has changed using fabs


class Brainbot:
    ######## CHANGE THE FOLLOWING VALUES #########
    SERVER_PUBLIC_DNS = 'http://ip_server/'  # must start with http:// .  Don't include a trailing "/"
    NEAR_DOCKING_STATION_X = 0.75  # x coordinate for pose approx 1 mhttp://ec2-54-200-33-28.us-west-2.compute.amazonaws.cometer from docking station
    NEAR_DOCKING_STATION_Y = 0.15  # y coordinate for pose approx 1 meter http://localhost/turtlebot-server/from docking station
    ######## END CHANGE THE FOLLOWING VALUES #########

    ####### OPTIONVAL VALUES TO CHANGE ##########
    KOBUKI_BASE_MAX_CHARGE = 163
    # we're using the extended battery.  Your battery may have a different max charge value.  The maximum charge for kobuki base can be determined by running:
    # rostopic echo /mobile_base/sensors/core
    # and viewing the "battery" value.  This value is used to determine kobuki's battery status %.
    ####### END OPTIONVAL VALUES TO CHANGE ##########

    # defaults
    battery_is_low = False  # is kobuki's battery low?
    KOBUKI_PREVIOUS_BATTERY_LEVEL = 1000  # 1000 isn't possible.  Just a large fake # so the script starts believing the battery is fine
    charging_at_dock = False  # can't leave docking station until it's full because battery was low
    proactive_charging_at_dock = False  # can leave dock as soon as a request comes in because battery is fine
    count_no_one_needs_robot = 0  # keeps track of how many times in a row we receive "no one needs robot", after task finished.
    COUNT_BEFORE_PROACTIVE_CHARGING = 120  # 120 * 2 = 4 minutes d'inactivite apres TERMINER avant l'autodocking
    MAX_IN_USE_TIME = 600  # 10 minutes en avant TERMINER (en cours d'utilisation) avant l'autodocking
    temps_debut_utilisation = 0
    cannot_move_while_in_use = False  # is the tablet beeing used, so the robot shouldn't move
    autodocking_client = actionlib.SimpleActionClient('/dock_drive_action', AutoDockingAction)
    MAX_TIME_PER_TRY = rospy.Duration(40)  # time given to the robot the reach a certain pose (seconds)
    MAX_TRIES_PER_GOAL = 3  # number of retries in case of failure
    number_of_tries = 0
    ANGLES_IN_QUATER = True

    # table of coordinates
    # like: ((X, Y, Z), (Quaternion)), write FLOATS !
    COORDINATES = {
        0: ((0., 0., 0.), (0., 0., 0., 0.)),
        1: ((0.05, -0.77, 0.), (0., 0., 0.63, 0.77)),
        2: ((6.37, -1.8, 0.), (0., 0., 0.97, 0.2)),
        3: ((3.6, -3.2, 0.), (0., 0., 0.46, 0.88)),
        4: ((-0.84, -3.05, 0.), (0., 0., 0.26, 0.96)),
        5: ((8.9, -6.1, 0.), (0., 0., -1.4, 0.)),
        6: ((7.4, -16.0, 0.), (0., 0., 3.3, 0.)),
        7: ((3.7, 13.4, 0.), (0., 0., -0.2, 0.)),
    }

    # table of location names
    LOCATIONS = {
        0: "Terminer",
        1: "Autodocking",
        2: "Billets",
        3: "Porte Gauche",
        4: "Porte Droite",
        5: "Reseau 93",
        6: "Salon au fond",
        7: "Entree",
    }

    def __init__(self):
        # initialize ros node
        rospy.init_node('turtlebot_mdph_move', anonymous=False)

        # what to do if shut down (e.g. ctrl + C or failure)
        rospy.on_shutdown(self.shutdown)

        # tell the action client that we want to spin a thread by default
        self.move_base = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        rospy.loginfo("[MDPHLOG] Attente d'une reponse du server")
        # allow up to 3 seconds for the action server to come up
        self.move_base.wait_for_server(rospy.Duration(3))

        # monitor Kobuki's power and charging status.  If an event occurs (low battery, charging, not charging etc)
        # call function power_sensor_event_callback
        rospy.Subscriber("/mobile_base/sensors/core", SensorState, self.power_sensor_event_callback)

        # to avoid TurtleBot from driving to another pose while someone is making coffee ... TurtleBot isn't allowed
        # to move until the person presses the B0 button.  To implement this we need to monitor the kobuki button events
        rospy.Subscriber("/mobile_base/events/button", ButtonEvent, self.button_event_callback)

        # we empty the queue
        self.delete_queue_on_boot()

    def deliver_tablet(self):
        # if someone is using the robot, don't move
        # Check if someone said that the task was complete
        if self.in_use():
            time.sleep(3)
            return True

        rospy.loginfo("[MDPHLOG] Robot libre, en attente de commande...")

        # before execute the next command, how is power looking? If low go recharge first at the docking station.
        if self.do_we_need_power():
            return True

        # Power is fine so let's see if anyone needs the tablet...
        # rospy.loginfo("[MDPHLOG] Personne ne veut voir R2D3 ?")

        # call the server and "pop" the next pending customer's pose (if one is pending) from the stack
        data = json.load(urllib2.urlopen(self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?pop"))

        # check if we do have a pending command:
        if data["status"] != "pending":
            self.count_no_one_needs_robot += 1  # increment so we know how many times in a row no one needed the tablet
            rospy.loginfo("[MDPHLOG] Personne n'a besoin du robot #" + str(self.count_no_one_needs_robot))

            # considering there is nothing to do... should we charge?
            if self.count_no_one_needs_robot > self.COUNT_BEFORE_PROACTIVE_CHARGING and not self.charging_at_dock:
                rospy.loginfo("[MDPHLOG] Batterie ok, mais inactif trop longtemps, allons au dock.")
                self.dock_with_charging_station()  # tell TurtleBot to dock with the charging station
                self.proactive_charging_at_dock = True
            else:
                time.sleep(2)  # wait 2 seconds before asking the server if there are pending tablet needs

            return True

        command_number = int(data["point"]["x"])

        # deleting the number 7 commands, as TERMINER has already been pressed
        if command_number == 0:
            json.load(urllib2.urlopen(self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                "id"] + "&status=complete"))
            return True

        # if autodocking command
        elif command_number == 1:
            rospy.loginfo("[MDPHLOG] Commande autodocking recue, lancement...")
            self.dock_with_charging_station()  # tell TurtleBot to dock with the charging station
            json.load(urllib2.urlopen(self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                "id"] + "&status=complete"))
            return True

        else:  # someone is asking the tablet!  let's move!
            # If we're at the charging station back up 0.2 meters to avoid collision with dock
            self.do_we_need_to_back_up_from_dock()

            # now sure that it is not charging
            self.proactive_charging_at_dock = False
            self.charging_at_dock = False

            # get the goal according to the command number
            goal = self.get_goal_from_command_number(command_number)
            self.move_base.send_goal(goal)
            finished_in_time = self.move_base.wait_for_result(self.MAX_TIME_PER_TRY)

            # get the status after having waited
            goal_state = self.move_base.get_state()

            # reset variable no matter what the result is because the robot is not inactive anymore
            self.count_no_one_needs_robot = 0

            if goal_state != GoalStatus.SUCCEEDED:
                # failed to reach goal (e.g. TurtleBot can't find a way to go to the location)
                self.move_base.cancel_goal()
                self.number_of_tries += 1
                rospy.loginfo("[MDPHLOG] La base n'a pas reussi a atteindre la position desiree #" + str(self.number_of_tries))

                if self.number_of_tries >= self.MAX_TRIES_PER_GOAL:
                    rospy.loginfo("[MDPHLOG] Abandon de cet objectif.")
                    # tell the server that this pose is complete anyway (so it won't try it again)
                    json.load(urllib2.urlopen(
                        self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                            "id"] + "&status=complete"))
                    self.number_of_tries = 0
            else:
                rospy.loginfo("[MDPHLOG] Hooray, on a atteint la position desiree!")
                self.number_of_tries = 0
                # starting the use of the tablet
                self.cannot_move_while_in_use = True
                # save the time at wich the use started
                self.temps_debut_utilisation = time.time()
                # tell the server that the pose was completed
                json.load(urllib2.urlopen(
                    self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                        "id"] + "&status=complete"))

        return True

    def button_event_callback(self, data):
        # From https://github.com/yujinrobot/kobuki/blob/f99e495b2b3be1e62495119809c58ccb58909f67/kobuki_testsuite/scripts/test_events.py
        if data.button == ButtonEvent.Button0:
            self.cannot_move_while_in_use = False
            rospy.loginfo("[MDPHLOG] Boutton B0 appuye.")

    def do_we_need_to_back_up_from_dock(self):
        # if you set a goal while it's docked it tends to run into the docking station while turning.  
        # Tell it to back up a little before initiliazing goals.
        if self.charging_at_dock:
            rospy.loginfo("[MDPHLOG] Nous sommes au dock, reculons nous d'abord.")
            cmd_vel = rospy.Publisher('cmd_vel_mux/input/navi', Twist, queue_size=10)
            # Twist is a datatype for velocity
            move_cmd = Twist()
            # let's go forward at 0.1 m/s
            move_cmd.linear.x = -0.1
            # let's turn at 0 radians/s
            move_cmd.angular.z = 0

            r = rospy.Rate(10)
            # as long as you haven't ctrl + c keeping doing...
            temp_count = 0
            # go back at 0.1 m/s for 2 seconds
            while not rospy.is_shutdown() and temp_count < 20:
                # publish the velocity
                cmd_vel.publish(move_cmd)
                # wait for 0.1 seconds (10 HZ) and publish again
                temp_count = temp_count + 1
                r.sleep()
            # make sure TurtleBot stops by sending a default Twist()
            cmd_vel.publish(Twist())
            return True

    def do_we_need_power(self):
        # are we currently charging at the docking station?  If yes only continue if we're not fully charged
        if self.charging_at_dock and self.battery_is_low:
            rospy.loginfo("[MDPHLOG] Je dois me recharger avant de partir.")
            time.sleep(30)
            return True
        # are we not currently charging and is either battery low?  If yes, go to docking station.
        if not self.charging_at_dock and self.battery_is_low:
            rospy.loginfo("[MDPHLOG] Batterie faible, allons nous docker.")
            self.dock_with_charging_station()  # tell TurtleBot to dock with the charging station
            return True
        return False

    def power_sensor_event_callback(self, data):
        # kobuki's batttery value tends to bounce up and down 1 constantly so only report if difference greater than 1
        if math.fabs(int(data.battery) - self.KOBUKI_PREVIOUS_BATTERY_LEVEL) > 2:
            rospy.loginfo("[MDPHLOG] La batterie kobuki est maintenant a : " + str(
                round(float(data.battery) / float(self.KOBUKI_BASE_MAX_CHARGE) * 100)) + "%")
            self.KOBUKI_PREVIOUS_BATTERY_LEVEL = int(data.battery)

        if int(data.charger) == 0:
            if self.charging_at_dock:
                rospy.loginfo("[MDPHLOG] Arret de la charge au dock.")
            self.charging_at_dock = False
        else:
            if not self.charging_at_dock:
                rospy.loginfo("[MDPHLOG] En charge au dock.")
            self.charging_at_dock = True

        if round(float(data.battery) / float(self.KOBUKI_BASE_MAX_CHARGE) * 100) < 50:
            if not self.battery_is_low:
                rospy.loginfo("[MDPHLOG] La batterie KOBUKI est trop faible !")
            self.battery_is_low = True
        # the logic of not using the same value (e.g. 50) for both the -battery is low- & -battery is fine- is that
        # it'll leave and immediatly return for more power.  The reason why we don't use == 100 is that we hope
        # that proactive charging between tablet deliveries will charge it soon and we don't want people waiting.
        elif round(float(data.battery) / float(self.KOBUKI_BASE_MAX_CHARGE) * 100) > 60:
            if self.battery_is_low:
                rospy.loginfo("[MDPHLOG] La batterie KOBUKI est a un bon niveau.")
            self.battery_is_low = False

    def dock_with_charging_station(self):
        # check if already charging
        if self.charging_at_dock:
            return True

        # before we can run auto-docking we need to be close to the docking station..
        if not self.go_close_to_dock():
            return False

        # We're close to the docking station... so let's dock
        return self.we_are_close_dock()

    def we_are_close_dock(self):
        # The following will start the AutoDockingAction which will automatically find and dock TurtleBot with 
        # the docking station as long as it's near the docking station when started
        rospy.loginfo("[MDPHLOG] En attente du server d'autodocking...")
        self.autodocking_client.wait_for_server()
        rospy.loginfo("[MDPHLOG] auto_docking server found")
        goal = AutoDockingGoal()
        rospy.loginfo(
            "[MDPHLOG] Envoi de l'objectif autodocking et attente (180 secs), puis nouvelle tentative si necessaire.")
        self.autodocking_client.send_goal(goal)

        # Give the auto docking script 180 seconds.  It can take a while if it retries.
        success = self.autodocking_client.wait_for_result(rospy.Duration(180))

        if success:
            rospy.loginfo("[MDPHLOG] Succes de l'autodocking !")
            # The callback which detects the docking status can take up to 3 seconds to update which was causing
            # brainbot to try and redock (presuming it failed) even when the dock was successful.
            # Therefore hardcoding this value after success.
            self.charging_at_dock = True
            return True
        else:
            rospy.loginfo("[MDPHLOG] Echec de l'autodocking.")
            return False

    def go_close_to_dock(self):
        # the auto docking script works well as long as you are roughly 1 meter from the docking station.
        # So let's get close first...
        rospy.loginfo("[MDPHLOG] Rapprochons nous du dock.")

        # get the autodocking goal
        goal = self.get_goal_from_command_number(1)

        # start moving
        self.move_base.send_goal(goal)

        # allow TurtleBot up to 60 seconds to get close to
        success = self.move_base.wait_for_result(self.MAX_TIME_PER_TRY)

        if not success:
            self.move_base.cancel_goal()
            rospy.loginfo("[MDPHLOG] Nous n'avons pas pu nous approcher du dock...")
            return False
        else:
            # We made it!
            state = self.move_base.get_state()
            if state == GoalStatus.SUCCEEDED:
                rospy.loginfo("[MDPHLOG] Super ! Nous avons atteint le dock !")
                return True

    def in_use(self):
        """Opens all the pending commands from the server to see if the TERMINER button has been pressed."""
        # If the user already pressed TERMINER / B0
        if not self.cannot_move_while_in_use:
            return False

        # Check if device has been inactive for long enough (see MAX_IN_USE_TIME)
        if time.time() - self.temps_debut_utilisation > self.MAX_IN_USE_TIME:
            self.cannot_move_while_in_use = False
            return False

        rospy.loginfo("[MDPHLOG] Attente de l'appui sur le bouton B0 ou TERMINER, utilisation en cours.")
        fini = False

        # we check the whole queue for the finished command
        while not fini:
            data = json.load(urllib2.urlopen(self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?pop"))
            if data["status"] == "pending":
                # if there is a command, consider it done so we analyse the next one
                if float(data["point"]["x"]) == 0:
                    self.cannot_move_while_in_use = False
                    rospy.loginfo("[MDPHLOG] Commande TERMINER recue, analyse de la prochaine commande dans la queue.")
                    # we have received the finished command
                    fini = True
                json.load(urllib2.urlopen(
                    self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                        "id"] + "&status=complete"))
                # we space the request a bit just in case
                time.sleep(0.5)
            else:
                # no pending command, let's wait
                rospy.loginfo("[MDPHLOG] Aucune commande TERMINER recue, attente...")
                return True

    def shutdown(self):
        rospy.loginfo("[MDPHLOG] Stop")

    def get_goal_from_command_number(self, command_number):
        # get the command caracteristics
        command_name = self.LOCATIONS[command_number]
        coordinates = self.COORDINATES[command_number]

        # build the goal to be sent
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()

        if not self.ANGLES_IN_QUATER:
            quat_angle = self.get_quaternion_from_z_angle(coordinates[1][2])

        else:
            quat_angle = Quaternion(coordinates[1][0], coordinates[1][1], coordinates[1][2], coordinates[1][3])

        # set a the Pose with the given coordinates
        goal.target_pose.pose = Pose(
            Point(coordinates[0][0], coordinates[0][1], coordinates[0][2]), quat_angle)

        rospy.loginfo("[MDPHLOG] Envoi de l'objectif: " + command_name)
        return goal

    def get_quaternion_from_z_angle(self, z_angle):
        # uses the built in tf transforms function
        return Quaternion(*quaternion_from_euler(0, 0, z_angle, axes='sxyz'))

    def delete_queue_on_boot(self):
        # first variable to enter the loop
        empty_queue = False
        while not empty_queue:
            data = json.load(urllib2.urlopen(self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?pop"))
            if data["status"] == "pending":
                # consider the command done
                json.load(urllib2.urlopen(
                    self.SERVER_PUBLIC_DNS + "/turtlebot-server/coffee_queue.php?update&id=" + data[
                        "id"] + "&status=complete"))
                # we space the request a bit just in case
                time.sleep(0.2)
            else:
                # no pending command, empty queue
                rospy.loginfo("[MDPHLOG] Queue videe.")
                empty_queue = True


if __name__ == '__main__':
    delivery_checks = 0  # just for troubleshooting to see how many times we called the server for a new delivery
    try:
        robot = Brainbot()
        # keep checking for deliver_tablet until we shutdown the script with ctrl + c
        while robot.deliver_tablet() and not rospy.is_shutdown():
            delivery_checks += 1

    except rospy.ROSInterruptException:
        rospy.loginfo("[MDPHLOG] Exception thrown")
