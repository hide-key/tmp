# MOUSEKEY_ENABLE = yes       # Mouse keys
# EXTRAKEY_ENABLE = yes       # Audio control and System control
# CONSOLE_ENABLE = yes        # Console for debug
# COMMAND_ENABLE = yes        # Commands for debug and configuration

CUSTOM_MATRIX = yes
SRC += matrix.c

CFLAGS += -Ilib/pico-sdk/src/

CFLAGS += -Ilib/pico-sdk/src/host/pico_stdio/include/
CFLAGS += -Ilib/pico-sdk/src/rp2_common/pico_stdio/include/
CFLAGS += -Ilib/pico-sdk/src/common/pico_stdlib/include/
CFLAGS += -Ilib/pico-sdk/src/common/pico_time/include/

CFLAGS += -Ilib/pico-sdk/src/host/hardware_uart/include/
CFLAGS += -Ilib/pico-sdk/src/rp2_common/hardware_uart/include/

# CFLAGS += -Wno-strict-prototypes
# CFLAGS += -Wno-strict-prototypes -Wno-error
# CFLAGS += -Wno-implicit-function-declaration
