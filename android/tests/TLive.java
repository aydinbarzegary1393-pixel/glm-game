import com.glmgame.fps.UpdaterCore;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

/** Live end-to-end: UpdaterCore against real GitHub Pages manifest + files. */
public class TLive {
    static int fails = 0;
    static void check(String n, boolean ok) { check(n, ok, null); }
    static void check(String n, boolean ok, Object d) {
        System.out.println((ok ? "PASS " : "FAIL ") + n + (d != null ? " | " + d : ""));
        if (!ok) fails++;
    }
    public static void main(String[] a) throws Exception {
        final String BASE = "https://aydinbarzegary1393-pixel.github.io/glm-game/";
        byte[] mf = get(BASE + "version.json?t=" + System.currentTimeMillis());
        String json = new String(mf, StandardCharsets.UTF_8);
        String ver = UpdaterCore.extractString(json, "version");
        String[][] files = UpdaterCore.extractFiles(json);
        check("L1 live manifest fetched", ver != null && files.length >= 20, ver + " / " + files.length + " files");

        Path local = Files.createTempDirectory("glm-live");
        final int[] progress = {0};
        long t0 = System.currentTimeMillis();
        boolean ok = UpdaterCore.applyUpdate(json, BASE, local.toFile(),
            new UpdaterCore.Fetcher() { public byte[] get(String u) throws IOException { return TLive.get(u); } },
            new UpdaterCore.Logger() {
                public void stage(String fa, String en) { }
                public void progress(int p) { if (p > progress[0]) progress[0] = p; }
            });
        long dt = System.currentTimeMillis() - t0;
        check("L2 full update applied", ok, (dt / 1000.0) + "s, progress reached " + progress[0] + "%");

        // verify every file locally matches the manifest hashes
        int verified = 0;
        for (String[] f : files) {
            File f2 = local.resolve(f[0]).toFile();
            if (UpdaterCore.fileMatches(f2, f[1])) verified++;
        }
        check("L3 all files hash-verified on disk", verified == files.length, verified + "/" + files.length);
        check("L4 version.json adopted", ver.equals(UpdaterCore.extractString(
                new String(Files.readAllBytes(local.resolve("version.json")), StandardCharsets.UTF_8), "version")));

        // re-run: zero network fetches needed
        long t1 = System.currentTimeMillis();
        boolean ok2 = UpdaterCore.applyUpdate(json, BASE, local.toFile(),
            new UpdaterCore.Fetcher() { public byte[] get(String u) throws IOException { throw new IOException("should not fetch"); } },
            new UpdaterCore.Logger() { public void stage(String fa, String en) {} public void progress(int p) {} });
        check("L5 re-run = already up to date (no fetch)", ok2 && System.currentTimeMillis() - t1 < 5000);

        // offline behaviour: empty local dir + throwing fetcher -> abort, not throw
        Path empty = Files.createTempDirectory("glm-empty");
        boolean ok3 = UpdaterCore.applyUpdate(json, BASE, empty.toFile(),
            new UpdaterCore.Fetcher() { public byte[] get(String u) throws IOException { throw new IOException("offline"); } },
            new UpdaterCore.Logger() { public void stage(String fa, String en) {} public void progress(int p) {} });
        check("L6 offline-safe (keeps old)", !ok3 && Files.notExists(empty.resolve("version.json")));

        System.out.println(fails == 0 ? "\n==== LIVE ALL PASS ====" : "\n==== " + fails + " FAILURES ====");
        System.exit(fails == 0 ? 0 : 1);
    }
    static byte[] get(String u) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
        c.setConnectTimeout(5000); c.setReadTimeout(20000);
        c.setRequestProperty("Cache-Control", "no-cache");
        check200(c.getResponseCode());
        byte[] b = readAll(c.getInputStream());
        c.disconnect();
        return b;
    }
    static void check200(int code) throws IOException { if (code < 200 || code >= 300) throw new IOException("HTTP " + code); }
    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        byte[] ch = new byte[8192]; int n;
        while ((n = in.read(ch)) > 0) b.write(ch, 0, n);
        return b.toByteArray();
    }
}
