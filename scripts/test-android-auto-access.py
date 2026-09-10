#!/usr/bin/env python3
"""Exercise the production Android Auto gate with Python 3 and JDK 17's jshell.

This isolated regression needs no Android SDK, Gradle build, or dependency jars.
It runs the actual gate and its developer-check helper, with fixtures only for
the clock, build type, and app/version inputs. It does not validate APK packaging
or rendering through an Automotive templates host.
"""

from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "OsmAnd/src/net/osmand/plus/inapp/InAppPurchaseUtils.java"


def method(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
        end += 1
    return source[start:end]


def main():
    jshell = shutil.which("jshell")
    if not jshell:
        sys.exit("JDK 17+ jshell must be on PATH")

    source = SOURCE.read_text()
    constant = re.search(
        r"private static final long ANDROID_AUTO_START_DATE_MS\s*=.*?;", source
    ).group()
    gate = method(source, "public static boolean isAndroidAutoAvailable(")
    developer_check = method(source, "private static boolean checkDeveloperBuildIfNeeded(")

    fixture = r"""
class AndroidAutoAccessFixture {
    @interface NonNull {}
    static class OsmandApplication {}
    static class BuildConfig { static String BUILD_TYPE; }
    static class System {
        static long now;
        static long currentTimeMillis() { return now; }
    }
    static class Version {
        static long installed, updated;
        static boolean developer, paid;
        static long getInstallTime(OsmandApplication app) { return installed; }
        static long getUpdateTime(OsmandApplication app) { return updated; }
        static boolean isDeveloperBuild(OsmandApplication app) { return developer; }
        static boolean isPaidVersion(OsmandApplication app) { return paid; }
    }
    // Insert production code verbatim: no reimplementation of the access rule.
    __PRODUCTION__

    static int checked, failed;
    static final long DAY = 24L * 60 * 60 * 1000;
    static final long FIRST_USE = 1787599631101L;

    static void check(String name, String buildType, long elapsed, long updateOffset,
                      boolean developer, boolean paid, boolean expected) {
        BuildConfig.BUILD_TYPE = buildType;
        System.now = FIRST_USE + elapsed;
        Version.installed = FIRST_USE;
        Version.updated = FIRST_USE + updateOffset;
        Version.developer = developer;
        Version.paid = paid;
        boolean actual = isAndroidAutoAvailable(new OsmandApplication());
        checked++;
        if (actual != expected) {
            failed++;
            java.lang.System.out.println("FAIL: " + name + " expected " + expected
                    + " but was " + actual);
        }
    }

    static void run() {
        // Unentitled Automotive/Nightly must keep working beyond the old trial.
        check("automotive fresh", "automotive", 0, 0, false, false, true);
        check("automotive day ten", "automotive", 10 * DAY, 0, false, false, true);
        check("automotive observed day sixteen", "automotive", 16 * DAY, 0, false, false, true);
        check("automotive long after install", "automotive", 365 * DAY, 0, false, false, true);

        // The build type is not the package name, paid flavor, or debug flag.
        for (String type : new String[] {"debug", "release", "automotiveRelease"}) {
            check(type + " before deadline", type, 10 * DAY - 1, 0, false, false, true);
            check(type + " at deadline", type, 10 * DAY, 0, false, false, false);
            check(type + " after deadline", type, 16 * DAY, 0, false, false, false);
            check(type + " paid", type, 16 * DAY, 0, false, true, true);
            check(type + " developer", type, 16 * DAY, 0, true, false, true);
            check(type + " recent update", type, 16 * DAY, 15 * DAY, false, false, true);
            check(type + " update deadline", type, 25 * DAY, 15 * DAY, false, false, false);
            check(type + " install newer than update", type, 9 * DAY, -5 * DAY,
                    false, false, true);
        }
        if (failed != 0) {
            throw new AssertionError(failed + " of " + checked + " access cases failed");
        }
        java.lang.System.out.println("PASS: " + checked + " Android Auto access cases");
    }
}
AndroidAutoAccessFixture.run();
/exit
""".replace("__PRODUCTION__", "\n".join((constant, developer_check, gate)))

    result = subprocess.run(
        [jshell, "--feedback", "concise", "-"],
        input=fixture,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    print(result.stdout, end="")
    # jshell may exit zero even when a snippet fails to compile or throws.
    if result.returncode or "PASS: 28 Android Auto access cases" not in result.stdout:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
