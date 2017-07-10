package fr.cesgenslab.brainbot;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;

/**
 * Created by jerome on 12/06/2017.
 */

public class informationActivity extends Activity {
    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.information);

        ImageView buttonInformation =  (ImageView) findViewById(R.id.imageViewBackSeLoger);
        buttonInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(informationActivity.this, homeActivity.class);
                startActivity(myintent);
            }
        });

    }
}
