package fr.cesgenslab.brainbot;

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;

public class homeActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);

        setContentView(R.layout.activity_home);

        ImageView imageDossier =  (ImageView) findViewById(R.id.imageViewDossier);
        imageDossier.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(homeActivity.this, consulterDossierActivity.class);
                startActivity(myintent);
            }
        });

        ImageView imageInformation =  (ImageView) findViewById(R.id.imageViewInformation);
        imageInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(homeActivity.this, informationActivity.class);
                startActivity(myintent);
            }
        });

        ImageView imagejeux =  (ImageView) findViewById(R.id.imageViewJeux);
        imagejeux.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(homeActivity.this, jeuxWebAppActivity.class);
                startActivity(myintent);
            }
        });

        ImageView imageFormulaire =  (ImageView) findViewById(R.id.imageViewQuestion);
        imageFormulaire.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(homeActivity.this, formulaireWebAppActivity.class);
                startActivity(myintent);
            }
        });


    }
}
