package com.glmgame.fps;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Auto-update engine for the Android APK (pure java - testable on the JVM).
 *
 * Flow: fetch version.json manifest from GitHub Pages -> if its version is
 * newer than the running one, download ONLY the files whose SHA-256 differs
 * from the local copy, verify every download, write them atomically
 * (.tmp + rename) and store the new manifest as version.json LAST, so an
 * interrupted update never leaves a half-updated game claiming to be new.
 * Any failure keeps the old, fully playable version on the device.
 */
public class UpdaterCore {

    /** Downloads a URL and returns the body. Throws IOException on any failure. */
    public interface Fetcher {
        byte[] get(String url) throws IOException;
    }

    /** Localized progress reporting (fa = Farsi, en = English). */
    public interface Logger {
        void stage(String fa, String en);
        void progress(int percent);
    }

    /** strict semver: "v1.10.0" > "v1.9.0"; malformed values never compare newer. */
    public static boolean isNewer(String remote, String local) {
        long[] r = parse(remote), l = parse(local);
        if (r == null || l == null) return false;
        for (int i = 0; i < 3; i++) {
            if (r[i] != l[i]) return r[i] > l[i];
        }
        return false; // equal
    }

    private static long[] parse(String v) {
        if (v == null) return null;
        v = v.trim().toLowerCase();
        if (v.startsWith("v")) v = v.substring(1);
        String[] p = v.split("\\.");
        if (p.length < 1 || p.length > 3) return null;
        long[] out = new long[3];
        try {
            for (int i = 0; i < p.length; i++) {
                String part = p[i].trim();
                if (part.isEmpty()) return null;
                out[i] = Long.parseLong(part);
            }
        } catch (NumberFormatException e) {
            return null;
        }
        return out;
    }

    public static String extractString(String json, String key) {
        if (json == null || key == null) return null;
        Matcher m = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*\"([^\"]*)\"").matcher(json);
        return m.find() ? m.group(1) : null;
    }

    /**
     * Parses manifest "files" entries written by gen_version_manifest.py with
     * the FIXED key order {"path": "...", "sha256": "<64 hex>", "size": N}.
     * Returns rows of [path, sha256(lowercase), size].
     */
    public static String[][] extractFiles(String json) {
        ArrayList<String[]> out = new ArrayList<String[]>();
        if (json == null) return new String[0][];
        Matcher m = Pattern.compile(
                "\"path\"\\s*:\\s*\"([^\"]+)\"\\s*,\\s*\"sha256\"\\s*:\\s*\"([0-9a-fA-F]{64})\"\\s*,\\s*\"size\"\\s*:\\s*([0-9]+)")
                .matcher(json);
        while (m.find()) {
            out.add(new String[]{ m.group(1), m.group(2).toLowerCase(), m.group(3) });
        }
        return out.toArray(new String[0][]);
    }

    public static String sha256(byte[] data) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(data);
            StringBuilder sb = new StringBuilder(d.length * 2);
            for (byte b : d) {
                sb.append(Character.forDigit((b >> 4) & 0xF, 16));
                sb.append(Character.forDigit(b & 0xF, 16));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static boolean fileMatches(File f, String sha256Hex) {
        if (!f.isFile()) return false;
        FileInputStream in = null;
        try {
            in = new FileInputStream(f);
            return sha256(readAll(in)).equals(sha256Hex);
        } catch (IOException e) {
            return false;
        } finally {
            if (in != null) try { in.close(); } catch (IOException ignored) {}
        }
    }

    /**
     * Applies a manifest to targetDir. Returns true when the directory now
     * matches the manifest (version.json written). False = keep old version.
     */
    public static boolean applyUpdate(String manifestJson, String baseUrl, File targetDir,
                                      Fetcher fetcher, Logger log) {
        String remoteVer = extractString(manifestJson, "version");
        if (remoteVer == null || remoteVer.isEmpty()) return false;
        String[][] files = extractFiles(manifestJson);
        if (files.length == 0) return false;

        // which files are missing or differ?
        ArrayList<String[]> need = new ArrayList<String[]>();
        for (String[] f : files) {
            if (!fileMatches(new File(targetDir, f[0]), f[1])) need.add(f);
        }

        if (need.isEmpty()) {
            // content identical; just adopt the manifest
            log.stage("بازی به‌روز است", "Already up to date");
            return writeVersion(targetDir, manifestJson);
        }

        long bust = System.currentTimeMillis();
        int done = 0;
        for (String[] f : need) {
            log.stage("دانلود آپدیت… " + f[0], "Downloading update… " + f[0]);
            String url = baseUrl + f[0] + "?t=" + bust;
            byte[] data;
            try {
                data = fetcher.get(url);
            } catch (IOException e) {
                return false; // network died mid-update: keep the old version
            }
            if (!f[1].equals(sha256(data))) {
                return false; // corrupted download: abort, old version stays playable
            }
            if (!storeAtomically(targetDir, f[0], data)) return false;
            done++;
            log.progress((done * 100) / need.size());
        }

        // version marker LAST: a crash before this point just means "not updated"
        if (!writeVersion(targetDir, manifestJson)) return false;
        log.stage("آپدیت کامل شد", "Update complete");
        return true;
    }

    private static boolean storeAtomically(File targetDir, String relPath, byte[] data) {
        File t = new File(targetDir, relPath);
        File parent = t.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) return false;
        File tmp = new File(targetDir, relPath + ".tmp");
        FileOutputStream out = null;
        try {
            out = new FileOutputStream(tmp);
            out.write(data);
            out.flush();
            out.getFD().sync();
        } catch (IOException e) {
            return false;
        } finally {
            if (out != null) try { out.close(); } catch (IOException ignored) {}
        }
        if (!tmp.renameTo(t)) {
            // fallback: copy-move (rename across mount points can fail)
            FileInputStream fin = null;
            FileOutputStream fout = null;
            try {
                fin = new FileInputStream(tmp);
                fout = new FileOutputStream(t);
                byte[] chunk = new byte[16 * 1024];
                int n;
                while ((n = fin.read(chunk)) > 0) fout.write(chunk, 0, n);
                fout.flush();
                tmp.delete();
            } catch (IOException e) {
                return false;
            } finally {
                try { if (fin != null) fin.close(); } catch (IOException ignored) {}
                try { if (fout != null) fout.close(); } catch (IOException ignored) {}
            }
        }
        return true;
    }

    public static boolean writeVersion(File targetDir, String manifestJson) {
        return storeAtomically(targetDir, "version.json", manifestJson.getBytes());
    }

    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(16 * 1024);
        byte[] chunk = new byte[16 * 1024];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return buf.toByteArray();
    }
}
