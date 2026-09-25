package com.glmgame.fps;

import android.content.Context;
import android.content.res.AssetManager;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;

/**
 * Game file provider for the app: serves the UPDATED copy from
 * filesDir/game/ when present (downloaded by the updater), otherwise falls
 * back to the bundled copy inside the APK (assets/game/).
 */
public class AndroidSources implements GameServer.StreamSource {

    private final File localDir;
    private final AssetManager assets;

    public AndroidSources(Context ctx) {
        this.localDir = new File(ctx.getFilesDir(), "game");
        this.assets = ctx.getAssets();
    }

    @Override
    public InputStream open(String path) throws IOException {
        if (path == null) return null;
        path = path.replace('\\', '/');
        while (path.startsWith("/")) path = path.substring(1);
        if (path.isEmpty()) return null;

        // defense in depth: the server already rejects traversal, but never
        // trust a single layer - verify the canonical path stays inside localDir
        File f = new File(localDir, path);
        try {
            String canon = f.getCanonicalPath();
            if (canon.startsWith(localDir.getCanonicalPath() + File.separator) && f.isFile()) {
                return new BufferedInputStream(new FileInputStream(f));
            }
        } catch (IOException ignored) {
            // fall through to assets
        }

        try {
            return assets.open("game/" + path);
        } catch (FileNotFoundException e) {
            return null;
        }
    }
}
