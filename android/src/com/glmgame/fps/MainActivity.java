package com.glmgame.fps;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * GLM FPS - Android edition.
 *
 * Launch flow (per spec):
 *   1. show a splash screen
 *   2. if the device is online, check GitHub (Pages manifest) for a newer
 *      release; download only changed files, hash-verified
 *   3. when the update finishes (or immediately when offline / up-to-date /
 *      on any failure), start the game - it always runs from local files,
 *      fully offline, through the embedded HTTP server
 */
public class MainActivity extends Activity {

    private static final int PREFERRED_PORT = 8777;

    private GameServer server;
    private WebView web;
    private FrameLayout root;
    private LinearLayout splash;
    private TextView verText, statusFa, statusEn;
    private ProgressBar bar;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private String gameUrl;
    private boolean gameLaunched = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window w = getWindow();
        w.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        String bundledVersion = readBundledVersion();
        buildSplash(bundledVersion);
        setContentView(root);

        try {
            server = new GameServer(new AndroidSources(this), PREFERRED_PORT);
            server.start();
        } catch (Exception e) {
            statusFa.setText("خطا: سرور داخلی اجرا نشد");
            statusEn.setText("Error: internal server failed: " + e);
            return;
        }
        gameUrl = "http://127.0.0.1:" + server.getPort() + "/fps-game.html";

        // updater runs off the main thread; the UI only receives posted updates
        new Thread(new Runnable() {
            public void run() {
                new Updater(MainActivity.this).run(new Updater.Callbacks() {
                    public void stage(final String fa, final String en) {
                        ui.post(new Runnable() { public void run() {
                            if (statusFa != null) { statusFa.setText(fa); statusEn.setText(en); }
                        }});
                    }
                    public void percent(final int p) {
                        ui.post(new Runnable() { public void run() {
                            if (bar == null) return;
                            bar.setIndeterminate(false);
                            bar.setProgress(p);
                            statusFa.setText("دانلود آپدیت… ٪" + p);
                            statusEn.setText("Downloading update… " + p + "%");
                        }});
                    }
                    public void done(boolean updated, final String from, final String to, String error) {
                        ui.post(new Runnable() { public void run() { launchGame(); }});
                    }
                });
            }
        }, "glm-updater").start();
    }

    // ---------- game ----------

    private void launchGame() {
        if (gameLaunched) return;
        gameLaunched = true;
        statusFa.setText("در حال اجرای بازی…");
        statusEn.setText("Starting game…");

        web = new WebView(this);
        WebSettings st = web.getSettings();
        st.setJavaScriptEnabled(true);
        st.setDomStorageEnabled(true);                    // HUD layout + player settings
        st.setMediaPlaybackRequiresUserGesture(false);    // game audio may autoplay
        st.setTextZoom(100);                              // ignore system font scale
        st.setAllowFileAccess(true);
        st.setSupportZoom(false);
        st.setLoadWithOverviewMode(true);
        st.setUseWideViewPort(true);
        web.setBackgroundColor(Color.BLACK);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setVerticalScrollBarEnabled(false);
        web.setHorizontalScrollBarEnabled(false);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView v, String url) {
                // game rendered: fade the splash away
                splash.animate().alpha(0f).setDuration(400)
                        .withEndAction(new Runnable() { public void run() {
                            splash.setVisibility(View.GONE);
                        }}).start();
            }
        });

        root.addView(web, 0, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        web.loadUrl(gameUrl);
    }

    @Override
    public void onBackPressed() {
        // never kill the game accidentally: minimize instead of exit
        moveTaskToBack(true);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUi();
    }

    private void hideSystemUi() {
        View decor = getWindow().getDecorView();
        decor.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    }

    @Override
    protected void onDestroy() {
        if (server != null) server.stop();
        if (web != null) web.destroy();
        super.onDestroy();
    }

    // ---------- splash UI (built in code: no layout xml needed) ----------

    private void buildSplash(String version) {
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#05070d"));

        splash = new LinearLayout(this);
        splash.setOrientation(LinearLayout.VERTICAL);
        splash.setGravity(Gravity.CENTER);
        splash.setBackgroundColor(Color.parseColor("#05070d"));
        int pad = dp(28);
        splash.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("GLM FPS");
        title.setTextColor(Color.parseColor("#4fc3f7"));
        title.setTextSize(34);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setLetterSpacing(0.15f);
        title.setGravity(Gravity.CENTER);
        splash.addView(title);

        verText = new TextView(this);
        verText.setText(version + "  •  Auto-Update");
        verText.setTextColor(Color.parseColor("#5a6b7d"));
        verText.setTextSize(12);
        verText.setGravity(Gravity.CENTER);
        verText.setPadding(0, dp(6), 0, dp(28));
        splash.addView(verText);

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(dp(240), ViewGroup.LayoutParams.WRAP_CONTENT);
        bp.gravity = Gravity.CENTER_HORIZONTAL;
        bar.setIndeterminate(true);
        splash.addView(bar, bp);

        statusFa = new TextView(this);
        statusFa.setText("در حال بررسی به‌روزرسانی…");
        statusFa.setTextColor(Color.WHITE);
        statusFa.setTextSize(15);
        statusFa.setGravity(Gravity.CENTER);
        statusFa.setPadding(0, dp(24), 0, 0);
        splash.addView(statusFa);

        statusEn = new TextView(this);
        statusEn.setText("Checking for updates…");
        statusEn.setTextColor(Color.parseColor("#8a97a5"));
        statusEn.setTextSize(11);
        statusEn.setGravity(Gravity.CENTER);
        statusEn.setPadding(0, dp(4), 0, 0);
        splash.addView(statusEn);

        root.addView(splash, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    private String readBundledVersion() {
        InputStream in = null;
        try {
            in = getAssets().open("game/version.json");
            String json = new String(readAll(in), StandardCharsets.UTF_8);
            String v = UpdaterCore.extractString(json, "version");
            return (v == null || v.isEmpty()) ? "?" : v;
        } catch (Exception e) {
            return "?";
        } finally {
            if (in != null) try { in.close(); } catch (Exception ignored) {}
        }
    }

    private static byte[] readAll(InputStream in) throws java.io.IOException {
        java.io.ByteArrayOutputStream buf = new java.io.ByteArrayOutputStream(8 * 1024);
        byte[] chunk = new byte[8 * 1024];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return buf.toByteArray();
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
