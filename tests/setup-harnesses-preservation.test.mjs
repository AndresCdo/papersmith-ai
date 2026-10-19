import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(new URL("../scripts/setup-harnesses.sh", import.meta.url));
const HARNESSES = [".claude", ".pi", ".opencode", ".agents"];

function fixture(t, canonical = true) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "harness preservation-"));
  t.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const root = path.join(base, "repo");
  const bin = path.join(base, "bin");
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.mkdirSync(bin);
  fs.copyFileSync(SCRIPT, path.join(root, "scripts/setup-harnesses.sh"));
  if (canonical) {
    fs.mkdirSync(path.join(root, "skills/example"), { recursive: true });
    fs.writeFileSync(path.join(root, "skills/example/SKILL.md"), "canonical\n");
  }
  // Never execute real rm, even against the unfixed script. Simulate removal
  // by renaming the fixture entry intact, so destructive replacement is visible.
  fs.writeFileSync(path.join(bin, "rm"), `#!${process.execPath}
const fs = require("node:fs");
const path = require("node:path");
const args = process.argv.slice(2);
const target = args.at(-1);
const root = process.env.FIXTURE_ROOT;
const allowed = ${JSON.stringify(HARNESSES)}.map(h => path.join(root, h, "skills"));
if (args.length !== 2 || args[0] !== "-rf" || !allowed.includes(target)) process.exit(97);
fs.appendFileSync(process.env.RM_LOG, target + "\\n");
fs.renameSync(target, target + ".rm-preserved");
`, { mode: 0o755 });
  const log = path.join(base, "rm.log");
  fs.writeFileSync(log, "");
  return {
    root, base, log,
    run() {
      const result = spawnSync("bash", ["scripts/setup-harnesses.sh"], {
        cwd: root, encoding: "utf8", timeout: 10000,
        env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, FIXTURE_ROOT: root, RM_LOG: log },
      });
      assert.ifError(result.error);
      assert.notEqual(result.status, null, result.stderr);
      return result;
    },
  };
}

function snapshot(location) {
  let stat;
  try { stat = fs.lstatSync(location); } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
  if (stat.isSymbolicLink()) return { link: fs.readlinkSync(location), ino: stat.ino };
  if (stat.isDirectory()) return Object.fromEntries(fs.readdirSync(location).sort()
    .map(name => [name, snapshot(path.join(location, name))]));
  return { content: fs.readFileSync(location, "utf8") };
}

function refuseUnchanged(f, conflict) {
  const before = snapshot(f.root);
  const result = f.run();
  assert.deepEqual(snapshot(f.root), before, "refusal must preserve every entry before any mutation");
  assert.notEqual(result.status, 0, `must refuse ${conflict}; stdout: ${result.stdout}`);
  assert.ok(result.stderr.includes(conflict), result.stderr);
  assert.match(result.stderr, /move.*aside/i);
  assert.equal(fs.readFileSync(f.log, "utf8"), "", "must not invoke rm");
}

for (const harness of HARNESSES) {
  for (const kind of ["populated directory", "empty directory", "regular file", "live link", "dangling link", "indirect canonical link"]) {
    test(`${harness}: refuse and preserve ${kind}`, t => {
      const f = fixture(t);
      const parent = path.join(f.root, harness);
      const target = path.join(parent, "skills");
      fs.mkdirSync(parent);
      if (kind.endsWith("directory")) {
        fs.mkdirSync(target);
        if (kind.startsWith("populated")) fs.writeFileSync(path.join(target, "user.md"), "user content\n");
      } else if (kind === "regular file") {
        fs.writeFileSync(target, "user content\n");
      } else {
        const foreign = path.join(f.root, "foreign");
        if (kind === "live link") {
          fs.mkdirSync(foreign);
          fs.writeFileSync(path.join(foreign, "sentinel"), "preserve\n");
        } else if (kind === "indirect canonical link") {
          fs.symlinkSync("skills", foreign);
        }
        fs.symlinkSync("../foreign", target);
      }
      refuseUnchanged(f, target);
    });
  }

  for (const link of ["../skills", ".././skills/", "absolute"]) {
    test(`${harness}: preserve managed ${link} link as a no-op`, t => {
      const f = fixture(t);
      fs.mkdirSync(path.join(f.root, harness));
      const target = path.join(f.root, harness, "skills");
      fs.symlinkSync(link === "absolute" ? path.join(f.root, "skills") : link, target);
      const before = snapshot(target);
      for (let run = 0; run < 2; run++) {
        const result = f.run();
        assert.equal(result.status, 0, result.stderr);
        assert.deepEqual(snapshot(target), before, "managed link must not be replaced");
        assert.equal(fs.readFileSync(f.log, "utf8"), "");
        assert.equal(fs.existsSync(path.join(f.root, "skills/skills")), false, "no nested links");
      }
    });
  }

  for (const kind of ["live", "dangling"]) {
    test(`${harness}: reject ${kind} symlink parent before touching external content`, t => {
      const f = fixture(t);
      const external = path.join(f.base, "external");
      if (kind === "live") {
        fs.mkdirSync(path.join(external, "skills"), { recursive: true });
        fs.writeFileSync(path.join(external, "skills/sentinel"), "external content\n");
      }
      fs.symlinkSync(external, path.join(f.root, harness));
      const before = snapshot(external);
      const result = f.run();
      assert.deepEqual(snapshot(external), before, "external sentinel must remain untouched");
      assert.notEqual(result.status, 0, result.stdout);
      assert.ok(result.stderr.includes(path.join(f.root, harness)), result.stderr);
      assert.match(result.stderr, /move.*aside/i);
      for (const earlier of HARNESSES.slice(0, HARNESSES.indexOf(harness))) {
        assert.equal(snapshot(path.join(f.root, earlier)), null, "preflight before earlier mkdir/link");
      }
      assert.equal(fs.readFileSync(f.log, "utf8"), "");
    });
  }
}

test("absent targets get relative links, and repeated setup is a no-op", t => {
  const f = fixture(t);
  const first = f.run();
  assert.equal(first.status, 0, first.stderr);
  for (const harness of HARNESSES) {
    assert.equal(fs.readlinkSync(path.join(f.root, harness, "skills")), "../skills");
    assert.equal(fs.readFileSync(path.join(f.root, harness, "skills/example/SKILL.md"), "utf8"), "canonical\n");
  }
  const before = snapshot(f.root);
  const second = f.run();
  assert.equal(second.status, 0, second.stderr);
  assert.deepEqual(snapshot(f.root), before);
  assert.equal(fs.readFileSync(f.log, "utf8"), "");
});

test("last destination conflict prevents earlier managed-link replacement and missing-parent creation", t => {
  const f = fixture(t);
  fs.mkdirSync(path.join(f.root, ".claude"));
  fs.symlinkSync(path.join(f.root, "skills"), path.join(f.root, ".claude/skills"));
  fs.mkdirSync(path.join(f.root, ".agents/skills"), { recursive: true });
  fs.writeFileSync(path.join(f.root, ".agents/skills/user.md"), "keep\n");
  refuseUnchanged(f, path.join(f.root, ".agents/skills"));
});

test("missing canonical directory refuses without creating harness parents", t => {
  const f = fixture(t, false);
  const before = snapshot(f.root);
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /canonical skills directory not found/);
  assert.ok(result.stderr.includes(path.join(f.root, "skills")), result.stderr);
  assert.deepEqual(snapshot(f.root), before);
  assert.equal(fs.readFileSync(f.log, "utf8"), "");
});
