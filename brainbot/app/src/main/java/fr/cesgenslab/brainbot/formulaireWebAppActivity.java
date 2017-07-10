package fr.cesgenslab.brainbot;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.http.SslError;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.SslErrorHandler;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;

y
/**
 * Created by jerome on 13/06/2017.
 */

public class formulaireWebAppActivity extends webAppActivity {

    WebView mWebView;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.formulairewebapp);

        ImageView buttonInformation =  (ImageView) findViewById(R.id.imageViewBackFormulaireWebApp);
        buttonInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(formulaireWebAppActivity.this, homeActivity.class);
                startActivity(myintent);
            }
        });


        mWebView = (WebView) findViewById(R.id.webViewFormulaire);
        mWebView.setWebViewClient(new formulaireWebAppActivity.SSLTolerentWebViewClient());

        mWebView.getSettings().setJavaScriptEnabled(true);
        mWebView.loadUrl("https:/...server...turtlebot-web-app/formulaire.html");




        //mWebView.loadUrl("http://www.google.com");
    }


}
