// sv-tests: UVM DPI for clotho. Regex + command-line/report DPI are the real UVM
// C implementations; HDL-backdoor functions are stubbed (no VPI backend in clotho).
// uvm_svcmd_dpi.c (real UVM C, not stubbed) calls the VPI routine
// vpi_get_vlog_info to read $test$plusargs/argv; clotho has no VPI backend, so
// that one VPI entry point is stubbed here too, reporting no plusargs.
// Everything is forced to C linkage so DPI-C name lookup finds the plain symbols.
#include <limits.h>
#include <svdpi.h>

extern "C" {
#include "uvm_common.c"
#include "uvm_regex.cc"
#include "uvm_svcmd_dpi.c"

int uvm_hdl_check_path(char *path)                          { (void)path; return 0; }
int uvm_hdl_read(char *path, p_vpi_vecval value)            { (void)path; (void)value; return 0; }
int uvm_hdl_deposit(char *path, p_vpi_vecval value)         { (void)path; (void)value; return 0; }
int uvm_hdl_force(char *path, p_vpi_vecval value)           { (void)path; (void)value; return 0; }
int uvm_hdl_release(char *path)                             { (void)path; return 0; }
int uvm_hdl_release_and_read(char *path, p_vpi_vecval value){ (void)path; (void)value; return 0; }

PLI_INT32 vpi_get_vlog_info(p_vpi_vlog_info info) {
  info->argc = 0;
  info->argv = NULL;
  info->product = (PLI_BYTE8 *)"clotho";
  info->version = (PLI_BYTE8 *)"0.1";
  return 1;
}
}
