package fr.cesgenslab.brainbot;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.http.SslError;
import android.os.Bundle;
import android.support.annotation.LayoutRes;
import android.support.annotation.Nullable;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;

import java.lang.reflect.AccessibleObject;

/**
 * Created by jerome on 12/06/2017.
 *
 * Gestion de l'activité de la vue de consultation du dossier
 */

public class consulterDossierWebAppActivity extends webAppActivity {

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.consulterdossierwebapp);

        ImageView buttonInformation =  (ImageView) findViewById(R.id.imageViewBackConsulterWebApp);
        buttonInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(consulterDossierWebAppActivity.this, consulterDossierActivity.class);
                startActivity(myintent);
            }
        });


        Button buttonBack =  (Button) findViewById(R.id.boutonBack);
        buttonBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mWebView.goBack();
            }
        });


        mWebView = (WebView) findViewById(R.id.webViewConsulterDossier);
        mWebView.setWebViewClient(new SSLTolerentWebViewClient());
        mWebView.getSettings().setJavaScriptEnabled(true);
        mWebView.loadUrl("https://mesaides.seinesaintdenis.fr/connexion/");

    }
}
