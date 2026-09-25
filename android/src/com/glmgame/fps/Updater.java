package com.glmgame.fps;

import android.content.Context;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Android glue around UpdaterCore: knows the GitHub Pages URLs, reads the
 * local/bundled version, reports localized progress and finishes with a
 * single done() callback. Always succeeds in the sense that the game is
 * playable afterwards - any network failure simply means "keep old version".
 */
public class Updater {

    public static final String PAGES_BASE =
            "https://aydinbarzegary1393-pixel.github.io/glm-game/";
    public static final String MANIFEST_URL = PAGES_BASE + "version.json";

    public interface Callbacks {
        void stage(String fa, String en);
        void percent(int p);
        void done(boolean updated, String versionFrom, String versionTo, String error);
    }

    private final Context ctx;

    public Updater(Context ctx) {
        this.ctx = ctx.getApplicationContext();
    }

    public void run(final Callbacks cb) {
        try {
            runInternal(cb);
        } catch (Exception e) {
            // absolute last resort: never block the game from starting
            cb.done(false, "?", "?", String.valueOf(e));
        }
    }

    private void runInternal(Callbacks cb) throws IOException {
        File gameDir = new File(ctx.getFilesDir(), "game");
        if (!gameDir.isDirectory()) gameDir.mkdirs();

        String localVer = readLocalVersion(gameDir);
        cb.stage("در حال بررسی به‌روزرسانی…", "Checking for updates…");

        String manifestJson;
        try {
            byte[] mf = httpGet(MANIFEST_URL + "?t=" + System.currentTimeMillis(), 4000, 6000);
            manifestJson = new String(mf, StandardCharsets.UTF_8);
        } catch (IOException e) {
            cb.done(false, localVer, localVer, "offline");
            return;
        }

        String remoteVer = UpdaterCore.extractString(manifestJson, "version");
        if (remoteVer == null || !UpdaterCore.isNewer(remoteVer, localVer)) {
            cb.done(false, localVer, localVer, null);
            return;
        }

        cb.stage("نسخه جدید پیدا شد: " + remoteVer, "New version found: " + remoteVer);

        boolean ok = UpdaterCore.applyUpdate(manifestJson, PAGES_BASE, gameDir,
                new UpdaterCore.Fetcher() {
                    public byte[] get(String url) throws IOException {
                        return httpGet(url, 6000, 20000);
                    }
                },
                new UpdaterCore.Logger() {
                    public void stage(String fa, String en) { cb.stage(fa, en); }
                    public void progress(int p) { cb.percent(p); }
                });

        cb.done(ok, localVer, ok ? remoteVer : localVer, ok ? null : "update failed");
    }

    /** filesDir/game/version.json wins over the APK-bundled one. */
    private String readLocalVersion(File gameDir) {
        File local = new File(gameDir, "version.json");
        String json = null;
        if (local.isFile()) {
            FileInputStream in = null;
            try {
                in = new FileInputStream(local);
                json = new String(UpdaterCore.readAll(in), StandardCharsets.UTF_8);
            } catch (IOException ignored) {
            } finally {
                if (in != null) try { in.close(); } catch (IOException ignored) {}
            }
        }
        if (json == null) {
            InputStream in = null;
            try {
                in = ctx.getAssets().open("game/version.json");
                json = new String(UpdaterCore.readAll(in), StandardCharsets.UTF_8);
            } catch (IOException ignored) {
            } finally {
                if (in != null) try { in.close(); } catch (IOException ignored) {}
            }
        }
        String v = UpdaterCore.extractString(json, "version");
        return (v == null || v.isEmpty()) ? "0" : v;
    }

    static byte[] httpGet(String url, int connectTimeoutMs, int readTimeoutMs) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        try {
            c.setConnectTimeout(connectTimeoutMs);
            c.setReadTimeout(readTimeoutMs);
            c.setRequestProperty("Cache-Control", "no-cache");
            c.setInstanceFollowRedirects(true);
            int code = c.getResponseCode();
            if (code < 200 || code >= 300) throw new IOException("HTTP " + code + " for " + url);
            return readAll(c.getInputStream());
        } finally {
            c.disconnect();
        }
    }

    private static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(16 * 1024);
        byte[] chunk = new byte[16 * 1024];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return buf.toByteArray();
    }
}
