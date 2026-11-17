import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import leakgrep  # noqa: E402

TOOL = Path(leakgrep.__file__)

# Every sample is synthetic; none is taken from a game binary or a decompiler session.
POSITIVE = {
    'asm-mnemonic': ['    mov eax, [ebx+4]', '  push ebp', '00401000: call dword ptr [esi]', '// lea ecx, [esp+8]',
                     'cmp byte ptr [eax], 0', 'xor eax, eax', 'fld st(0)'],
    'decompiler-ident': ['int x = DAT_00abcdef;', 'goto LAB_0040aa10;', 'FUN_00412345(param_1);', 'undefined8 v;',
                         'undefined4 *p;', 'int a = local_1c;', 'x = in_EAX;', 'y = unaff_EBX;', 'iVar3 = 1;'],
    'hex-run': ['const char s[] = "' + 'ab' * 16 + '";', '00 11 22 33 44 55 66 77 88 99 aa bb cc dd ee ff',
                'u8 t[] = {0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08};', 's = "\\x90\\x90\\x90\\x90\\x90\\x90\\x90\\x90";'],
    'asm-directive': ['__asm { nop }', '__emit 0x90', 'asm("nop");', '_asm mov eax, 1', '#pragma code_seg(".text")',
                      '#pragma section(".x")', '#pragma comment(linker, "/export:x")', '__declspec(naked) void f();'],
    'private-path': ['// see /Users/someone/x', 'const char* p = "C:\\Users\\bob";', '#define P "/home/bob"',
                     'x = "C:/Users/bob";'],
    'include-outside-roots': ['#include "../x.h"', '#include "C:/x.h"', '#include "/etc/passwd"', '#include <windows.>',
                              '#include "foo.cpp"', '#include <vector.cpp>', '#include "a b.h"'],
}
NEGATIVE = {
    'asm-mnemonic': ['int mov = 1;', '// move the actor to the marker', 'return add(a, b);', 'push_back(x);',
                     '// call the destructor first', 'ret = sub(1, 2);'],
    'decompiler-ident': ['int undefined_behaviour = 0;', '// undefined behaviour here', 'int param = 1;', 'int local = 2;',
                         'int FUN = 3;', 'int input_x;', 'int Var3;'],
    'hex-run': ['unsigned id = 0x1575700;', 'u8 t[] = {0x01, 0x02, 0x03};', 'int a = 0xdeadbeef;', 'const char* s = "abcdef";',
                'u32 h = 0x1234abcd5678ef01;'],
    'asm-directive': ['// the assembler is not involved', 'int casm = 1;', 'void basement();', '#pragma once',
                      '#pragma pack(push, 4)'],
    'private-path': ['// the users of this class', 'int home = 1;', '#include "reconstruction/actor/Actor.h"'],
    'include-outside-roots': ['#include "reconstruction/actor/Actor.h"', '#include <cstdint>', '#include <stdint.h>',
                              '#include "Actor.h"'],
}


def diff_of(*lines, name='reconstruction/a/B.cpp'):
    body = ''.join('+' + l + '\n' for l in lines)
    return '--- /dev/null\n+++ b/%s\n@@ -0,0 +1,%d @@\n%s' % (name, len(lines), body)


class RuleCases(unittest.TestCase):
    def test_positive_samples_hit_their_rule(self):
        for code, lines in POSITIVE.items():
            for line in lines:
                with self.subTest(code=code, line=line):
                    self.assertIn(code, leakgrep.scan_line(line))

    def test_negative_samples_do_not_hit_their_rule(self):
        for code, lines in NEGATIVE.items():
            for line in lines:
                with self.subTest(code=code, line=line):
                    self.assertNotIn(code, leakgrep.scan_line(line))

    def test_relative_includes_are_judged_by_where_they_land(self):
        here = 'reconstruction/a/B.cpp'
        self.assertFalse(leakgrep.include_problem('#include "../b/C.h"', here))
        self.assertTrue(leakgrep.include_problem('#include "../../tools/C.h"', here))
        self.assertTrue(leakgrep.include_problem('#include "../../../x/C.h"', here))
        self.assertTrue(leakgrep.include_problem('#include "../b/C.h"'))

    def test_pinned_revision_labels_are_not_byte_dumps(self):
        self.assertEqual(leakgrep.scan_line('// COMMUNITY(owner/repo@' + 'ab12' * 10 + ', MIT)'), [])
        self.assertEqual(leakgrep.scan_line('// Origin: lib, MIT, ' + 'ab12' * 10 + '.'), [])
        self.assertIn('hex-run', leakgrep.scan_line('const char* s = "' + 'ab12' * 10 + '";'))
        self.assertIn('hex-run', leakgrep.scan_line('// ' + 'ab12' * 11))

    def test_private_names_come_from_the_list_only(self):
        self.assertEqual(leakgrep.scan_line('// by Zorblax', ('zorblax',)), ['private-name'])
        self.assertEqual(leakgrep.scan_line('// by Zorblax'), [])


class DiffHandling(unittest.TestCase):
    def test_only_added_lines_are_scanned_and_numbered(self):
        diff = ('--- a/reconstruction/a/B.cpp\n+++ b/reconstruction/a/B.cpp\n@@ -1,2 +5,3 @@\n'
                ' mov eax, [ebx]\n+int ok;\n+x = DAT_00aabbcc;\n-push ebp\n')
        self.assertEqual(leakgrep.scan_diff(diff), [('reconstruction/a/B.cpp', 7, 'decompiler-ident')])

    def test_deleted_file_is_ignored(self):
        diff = '--- a/x.cpp\n+++ /dev/null\n@@ -1 +0,0 @@\n-mov eax, [ebx]\n'
        self.assertEqual(leakgrep.scan_diff(diff), [])

    def test_odd_file_names_are_not_echoed(self):
        hits = leakgrep.scan_diff(diff_of('__emit 1', name='reconstruction/a/Evil name$(x).cpp'))
        self.assertEqual(hits, [('<file 1>', 1, 'asm-directive')])


class Cli(unittest.TestCase):
    def run_cli(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'p.diff'
            path.write_text(text)
            return subprocess.run([sys.executable, str(TOOL), '--diff', str(path), '--private-list', str(Path(d) / 'none')],
                                  capture_output=True, text=True)

    def test_clean_diff_exits_zero(self):
        r = self.run_cli(diff_of('int f() { return 1; }'))
        self.assertEqual((r.returncode, r.stdout), (0, 'leakgrep: 0 hit(s)\n'))

    def test_hit_exits_non_zero_with_code_and_line(self):
        r = self.run_cli(diff_of('int a;', 'mov eax, [ebx]'))
        self.assertEqual(r.returncode, 1)
        self.assertIn('reconstruction/a/B.cpp:2 asm-mnemonic', r.stdout)

    def test_output_never_echoes_matched_text(self):
        secrets = ['mov eax, [ebx+0x1c4]', 'DAT_0123abcd', 'ab' * 16, '__emit 0xCC', '/Users/zorblax/secret', 'FUN_00ff00ff']
        r = self.run_cli(diff_of(*secrets))
        self.assertEqual(r.returncode, 1)
        out = r.stdout + r.stderr
        for text in secrets + ['zorblax', 'ebx', '0123abcd', '00ff00ff', '0xCC']:
            self.assertNotIn(text, out)


if __name__ == '__main__':
    unittest.main()
