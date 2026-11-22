CONTIKI_PROJECT = acr_phy_tx acr_phy_rx
all: $(CONTIKI_PROJECT)
CONTIKI = ../..
MAKE_NET = MAKE_NET_NULLNET
MAKE_MAC = MAKE_MAC_CSMA
CFLAGS += -DENERGEST_CONF_ON=1 -I../../../arch/platform/iotlab/openlab
include $(CONTIKI)/Makefile.include
