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
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;

/**
 * Created by jerome on 13/06/2017.
 */

public class jeuxWebAppActivity extends webAppActivity {

    WebView mWebView;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.jeuxwebapp);

        ImageView buttonInformation =  (ImageView) findViewById(R.id.imageViewBackJeuxWebApp);
        buttonInformation.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent myintent = new Intent(jeuxWebAppActivity.this, homeActivity.class);
                startActivity(myintent);
            }
        });


        mWebView = (WebView) findViewById(R.id.webViewJeux);
        mWebView.clearCache(true);
        mWebView.clearHistory();
        mWebView.getSettings().setJavaScriptEnabled(true);
        mWebView.setWebViewClient(new jeuxWebAppActivity.SSLTolerentWebViewClient());
        mWebView.getSettings().setJavaScriptEnabled(true);
        mWebView.getSettings().setDomStorageEnabled(true);
        mWebView.setWebChromeClient(new WebChromeClient());
        mWebView.loadUrl("server html");

    }


}
