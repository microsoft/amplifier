# posix shell
rm_dir = rm -rf
rm_file = rm -rf
fix_path = $(1)
touch = touch $(1)
true_expression = true
stdout_redirect_null = 1>/dev/null
stderr_redirect_null = 2>/dev/null
stderr_redirect_stdout = 2>&1
command_exists = command -v $(1)

# windows shell
ifeq ($(suffix $(SHELL)),.exe)
rm_dir = rd /s /q
rm_file = del /f /q
fix_path = $(subst /,\,$(abspath $(1)))
# https://ss64.com/nt/touch.html
touch = type nul >> $(call fix_path,$(1)) && copy /y /b $(call fix_path,$(1))+,, $(call fix_path,$(1)) $(ignore_output)
true_expression = VER>NUL
stdout_redirect_null = 1>NUL
stderr_redirect_null = 2>NUL
stderr_redirect_stdout = 2>&1
command_exists = where $(1)
endif

ignore_output = $(stdout_redirect_null) $(stderr_redirect_stdout)
ignore_failure = || $(true_expression)
