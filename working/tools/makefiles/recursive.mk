# Runs make in all recursive subdirectories with a Makefile, passing the make target to each.
# Directories are make'ed in top down order.
# ex: make (runs DEFAULT_GOAL)
# ex: make clean (runs clean)
# ex: make install (runs install)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# if IS_RECURSIVE_MAKE is set, then this is being invoked by another recursive.mk.
# in that case, we don't want any targets
ifndef IS_RECURSIVE_MAKE

.DEFAULT_GOAL := help

# make with VERBOSE=1 to print all outputs of recursive makes
VERBOSE ?= 0

RECURSIVE_TARGETS = clean test check lock install

# You can pass in a list of files or directories to retain when running `clean/git-clean`
# ex: make clean GIT_CLEAN_RETAIN=".env .data"
# As always with make, you can also set this as an environment variable
GIT_CLEAN_RETAIN ?= .env
GIT_CLEAN_EXTRA_ARGS = $(foreach v,$(GIT_CLEAN_RETAIN),--exclude !$(v))
ifeq ($(VERBOSE),0)
GIT_CLEAN_EXTRA_ARGS += --quiet
endif


.PHONY: git-clean
git-clean:
	git clean -dffX . $(GIT_CLEAN_EXTRA_ARGS)

FILTER_OUT = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
MAKE_FILES = $(shell find . -mindepth 2 -name Makefile)
ALL_MAKE_DIRS = $(sort $(filter-out ./,$(dir $(MAKE_FILES))))
ifeq ($(suffix $(SHELL)),.exe)
MAKE_FILES = $(shell dir Makefile /b /s)
ALL_MAKE_DIRS = $(sort $(filter-out $(subst /,\,$(abspath ./)),$(patsubst %\,%,$(dir $(MAKE_FILES)))))
endif

# Filter out dependency and cache directories from recursive make targets
MAKE_DIRS_TMP := $(ALL_MAKE_DIRS)
MAKE_DIRS_TMP := $(call FILTER_OUT,node_modules,$(MAKE_DIRS_TMP))
MAKE_DIRS_TMP := $(call FILTER_OUT,site-packages,$(MAKE_DIRS_TMP))
MAKE_DIRS := $(call FILTER_OUT,.cache,$(MAKE_DIRS_TMP))

.PHONY: .clean-error-log .print-error-log

MAKE_CMD_MESSAGE = $(if $(MAKECMDGOALS), $(MAKECMDGOALS),)

.clean-error-log:
	@$(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure)

.print-error-log:
ifeq ($(suffix $(SHELL)),.exe)
	@if exist $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ( \
		echo Directories failed to make$(MAKE_CMD_MESSAGE): && \
		type $(call fix_path,$(mkfile_dir)/make_error_dirs.log) && \
		($(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure)) && \
		exit 1 \
	)
else
	@if [ -e $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ]; then \
		echo "\n\033[31;1mDirectories failed to make$(MAKE_CMD_MESSAGE):\033[0m\n"; \
		cat $(call fix_path,$(mkfile_dir)/make_error_dirs.log); \
		echo ""; \
		$(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure); \
		exit 1; \
	fi
endif

.PHONY: $(RECURSIVE_TARGETS) $(MAKE_DIRS)

clean: git-clean

$(RECURSIVE_TARGETS): .clean-error-log $(MAKE_DIRS) .print-error-log

$(MAKE_DIRS):
ifdef FAIL_ON_ERROR
	$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1
else
	@$(rm_file) $(call fix_path,$@/make*.log) $(ignore_output) $(ignore_failure)
	@echo make -C $@ $(MAKECMDGOALS)
ifeq ($(suffix $(SHELL)),.exe)
	@$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1 1>$(call fix_path,$@/make.log) $(stderr_redirect_stdout) || \
		( \
			(findstr /c:"*** No" $(call fix_path,$@/make.log) ${ignore_output}) || ( \
				echo $@ >> $(call fix_path,$(mkfile_dir)/make_error_dirs.log) && \
				$(call touch,$@/make_error.log) \
			) \
		)
	@if exist $(call fix_path,$@/make_error.log) echo make -C $@$(MAKE_CMD_MESSAGE) failed:
	@if exist $(call fix_path,$@/make_error.log) $(call touch,$@/make_print.log)
	@if "$(VERBOSE)" neq "0" $(call touch,$@/make_print.log)
	@if exist $(call fix_path,$@/make_print.log) type $(call fix_path,$@/make.log)
else
	@$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1 1>$(call fix_path,$@/make.log) $(stderr_redirect_stdout) || \
		( \
			grep -qF "*** No" $(call fix_path,$@/make.log) || ( \
				echo "\t$@" >> $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ; \
				$(call touch,$@/make_error.log) ; \
			) \
		)
	@if [ -e $(call fix_path,$@/make_error.log) ]; then \
		echo "\n\033[31;1mmake -C $@$(MAKE_CMD_MESSAGE) failed:\033[0m\n" ; \
	fi
	@if [ "$(VERBOSE)" != "0" -o -e $(call fix_path,$@/make_error.log) ]; then \
		cat $(call fix_path,$@/make.log); \
	fi
endif
	@$(rm_file) $(call fix_path,$@/make*.log) $(ignore_output) $(ignore_failure)
endif # ifdef FAIL_ON_ERROR

endif # ifndef IS_RECURSIVE_MAKE

include $(mkfile_dir)/shell.mk
