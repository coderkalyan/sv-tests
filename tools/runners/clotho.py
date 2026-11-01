#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import os
import shlex

from BaseRunner import BaseRunner


class clotho(BaseRunner):
    def __init__(self):
        # The vendored submodule under third_party/tools/clotho is on PATH ahead
        # of anything else, so a working tree's build is invisible by default and
        # the report silently measures whatever was last vendored. CLOTHO_BIN
        # points the runner at a specific binary instead.
        super().__init__(
            'clotho', os.environ.get('CLOTHO_BIN', 'clotho'),
            {'parsing', 'elaboration', 'simulation'})

        # Run from the test's :workdir: with its :scratch_dirs:, as the suite's
        # own driver does (ivtest's designs open "ivltests/..." and "work/...").
        self.uses_workdir = True

        self.submodule = "third_party/tools/clotho"
        self.url = f"https://github.com/chipsalliance/sv-tests/tree/{self.get_commit()}"

    def prepare_run_cb(self, tmp_dir, params):
        mode = params['mode']

        # clotho takes a subcommand, not a mode flag. `run` JIT-compiles and
        # simulates; `lint` parses and elaborates and stops. The front end fails
        # loudly on any construct it cannot lower, so a clean `lint` exit is a
        # real elaboration pass rather than a silent skip.
        self.cmd = [self.executable]

        if mode == 'simulation':
            self.cmd.append('run')
        else:
            self.cmd.append('lint')

        # UVM imports its regex / HDL-access helpers through DPI-C (LRM 35), and
        # `export "DPI-C" function m__uvm_report_dpi` (uvm_globals.svh) means the
        # UVM C calls back into the JIT-compiled design. clotho's JIT can only
        # patch such callbacks through a relocatable object, not a prebuilt .so
        # (whose internal calls are already bound) — see clotho --help on
        # --dpi-lib. tools/runners.mk pre-builds tests/<uvm>/src/dpi into a .o
        # with the regex functions real and the HDL-backdoor / VPI functions
        # stubbed (clotho has no VPI backend). Link it for a simulation of a UVM
        # test — `--dpi-lib` is a run-only flag, and only `run` JIT-links symbols.
        if mode == 'simulation':
            tags = params.get('tags', '').split()
            uvm_lib = 'uvm-1.2' if 'uvm-1.2' in tags else (
                'uvm' if 'uvm' in tags else None)
            if uvm_lib is not None:
                dpi = os.path.join(
                    os.environ.get('OUT_DIR', 'out'), 'runners', 'lib',
                    uvm_lib + '_dpi.o')
                if os.path.exists(dpi):
                    self.cmd += ['--dpi-lib', os.path.abspath(dpi)]

        # clotho forwards unrecognised flags to slang's Driver, so pass the
        # standard preprocessor/elaboration options through: include dirs, macro
        # defines and an explicit top module. Required by multi-file tests and
        # any design that uses `include (cores, UVM).
        for incdir in params['incdirs']:
            self.cmd.append('-I' + incdir)

        for define in params['defines']:
            self.cmd.append('-D' + define)

        if params['top_module'] != '':
            self.cmd += ['--top', params['top_module']]

        # Per-test clotho options, e.g. ":runner_clotho_flags: --loose-timescale"
        # for designs that legitimately mix timescale/no-timescale and would
        # otherwise be refused by clotho's strict-by-default check.
        if 'runner_clotho_flags' in params:
            self.cmd += shlex.split(params['runner_clotho_flags'])

        self.cmd += params['files']

        # `+arg`s after the files go to the design for $test$plusargs and
        # $value$plusargs (LRM 21.6); a `lint` has no run to give them to.
        if mode == 'simulation':
            self.cmd += params['plusargs']

    def get_version_cmd(self):
        return [self.executable, "--version"]
