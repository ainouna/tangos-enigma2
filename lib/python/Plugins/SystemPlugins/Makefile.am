installdir = $(pkglibdir)/python/Plugins/SystemPlugins

SUBDIRS = CEC PositionerSetup Satfinder \
	SkinSelector SatelliteEquipmentControl Videomode Hotplug \
	OSD3DSetup VFD-Icons

if HAVE_TEMPFANCONTROL
SUBDIRS += TempFanControl
endif

install_PYTHON =	\
	__init__.py
