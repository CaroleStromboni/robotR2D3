package fr.cesgenslab.brainbot;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;

/**
 * Created by jerome on 09/06/2017.
 *
 * Classe qui permet de gerer l'activité de la vue Consulter Dossier
 */

public class consulterDossierActivity extends Activity {
    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);

        setContentView(R.layout.consulter_dossier);


        ImageView imageInformation =  (ImageView) findViewById(R.id.imageViewRetour);
        imageInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(consulterDossierActivity.this, homeActivity.class);
                startActivity(myintent);
            }
        });


        ImageView buttonConsulter =  (ImageView) findViewById(R.id.imageViewconsulterdossier);
        buttonConsulter.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(consulterDossierActivity.this, consulterDossierWebAppActivity.class);
                startActivity(myintent);
            }
        });
    }
}
