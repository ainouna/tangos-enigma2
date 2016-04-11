from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference
from enigma import iPlayableService, iServiceInformation, iFrontendInformation, iRecordableService, eTimer, evfd, eDVBVolumecontrol, iTimeshiftServicePtr
from time import localtime, strftime, sleep
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Console import Console
from Tools.Directories import fileExists
from os import environ, statvfs
from Components.config import *
from Components.ServiceList import ServiceList

class VFDIcons():

    def __init__(self, session):
        self.session = session
        self.onClose = []
        self.timer = eTimer()
        self.timer.callback.append(self.timerEvent)
        self.timer.start(60000, False)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedInfo: self.UpdatedInfo,
         iPlayableService.evUpdatedEventInfo: self.__evUpdatedEventInfo,
         iPlayableService.evVideoSizeChanged: self.__evVideoSizeChanged,
         iPlayableService.evSeekableStatusChanged: self.__evSeekableStatusChanged,
         iPlayableService.evTunedIn: self.__evTunedIn,
         iPlayableService.evTuneFailed: self.__evTuneFailed,
         iPlayableService.evStart: self.__evStart})
        config.misc.standbyCounter.addNotifier(self.onEnterStandby, initial_call=False)
        session.nav.record_event.append(self.gotRecordEvent)
        self.tuned = False
        self.play = True
        self.timeshift = False
        self.record = False
        self.isMuted = False
        self.standby = False
        self.usb = 0
        self.mp3Available = False
        self.dolbyAvailable = False
        self.DTSAvailable = False
        tm = localtime()
        fp_time = strftime('%H:%M:%S %d-%m-%Y', tm)
        Console().ePopen('fp_control -s '+fp_time)
        try:
            from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
            hotplugNotifier.append(self.hotplugCB)
        except:
            pass

    def __evStart(self):
        print '[VFD-Icons] __evStart'
        self.__evSeekableStatusChanged()

    def __evUpdatedEventInfo(self):
        print '[VFD-Icons] __evUpdatedEventInfo'

    def UpdatedInfo(self):
        print '[VFD-Icons] __evUpdatedInfo'
        self.checkAudioTracks()
        self.WriteName()
        self.showDTS()
        self.showCrypted()
        self.showDolby()
        self.showMP3()
        self.showTuned()
        self.showMute()

    def WriteName(self):
                service = self.session.nav.getCurrentlyPlayingServiceOrGroup()
                if service:
                    path = service.getPath()
                    if path:
                        self.play = True
                        servicename = 'PLAY'
                        currPlay = self.session.nav.getCurrentService()
                        if currPlay != None and self.mp3Available:
                            servicename = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
                            Console().ePopen('fp_control -i 28 1 -i 27 0')
                        else:
                            self.service = self.session.nav.getCurrentlyPlayingServiceReference()
                            if self.service is not None:
                                service = self.service.toCompareString()
                                servicename = ServiceReference(service).getServiceName().replace('\xc2\x87', '').replace('\xc2\x86', '').ljust(16)
                                Console().ePopen('fp_control -i 27 1 -i 28 0')
                        Console().ePopen('fp_control -i 3 1')
                    else:
                        self.play = False
                        servicename = ServiceReference(service).getServiceName()
                        Console().ePopen('fp_control -i 3 0')
                        if config.servicelist.lastmode.value == 'tv':
                                Console().ePopen('fp_control -i 27 1 -i 28 0')
                        else:
                                Console().ePopen('fp_control -i 28 1 -i 27 0')
                    servicename = servicename.replace('+', '*')
                    servicename = servicename.replace('  ', ' ')
                    evfd.getInstance().vfd_write_string(servicename[0:63])
                    return

    def showCrypted(self):
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                crypted = info.getInfo(iServiceInformation.sIsCrypted)
                if crypted == 1:
                    Console().ePopen('fp_control -i 11 1')
                else:
                    Console().ePopen('fp_control -i 11 0')

    def checkAudioTracks(self):
        self.mp3Available = False
        self.dolbyAvailable = False
        self.DTSAvailable = False
        service = self.session.nav.getCurrentService()
        if service:
                audio = service.audioTracks()
                if audio:
                    n = audio.getNumberOfTracks()
                    for x in range(n):
                        i = audio.getTrackInfo(x)
                        description = i.getDescription()
                        if description.find('MP3') != -1:
                            self.mp3Available = True
                        if description.find('AC3') != -1:
                            self.dolbyAvailable = True
                        if description.find('DTS') != -1:
                            self.DTSAvailable = True

    def showDolby(self):
        if self.dolbyAvailable:
            Console().ePopen('fp_control -i 26 1')
        else:
            Console().ePopen('fp_control -i 26 0')

    def showMP3(self):
        if self.mp3Available:
            Console().ePopen('fp_control -i 25 1')
        else:
            Console().ePopen('fp_control -i 25 0')

    def showDTS(self):
        if self.DTSAvailable or self.dolbyAvailable:
            Console().ePopen('fp_control -i 10 1')
        else:
            Console().ePopen('fp_control -i 10 0')

    def showMute(self):
        self.isMuted = eDVBVolumecontrol.getInstance().isMuted()
        if self.isMuted:
            Console().ePopen('fp_control -i 8 1')
        else:
            Console().ePopen('fp_control -i 8 0')

    def showTuned(self):
            if self.tuned == True:
                service = self.session.nav.getCurrentService()
                if service:
                    info = service.info()
                    feinfo = service.frontendInfo()
                    data = info and info.getInfoObject(iServiceInformation.sTransponderData)
                    tunerType = data.get('tuner_type')
                    if tunerType == 'DVB-S':
                        print '[VFD-Icons] Set SAT icon'
                        Console().ePopen('fp_control -i 42 1 -i 37 0 -i 29 0')
                    elif tunerType == 'DVB-T' or tunerType == 'DVB-C':
                        print '[VFD-Icons] Set TER icon'
                        Console().ePopen('fp_control -i 37 1 -i 42 0 -i 29 0')
                    else:
                        print '[VFD-Icons] No TER or SAT icon'
                        Console().ePopen('fp_control -i 37 0 -i 42 0 -i 29 0')
            else:
                Console().ePopen('fp_control -i 37 0 -i 42 0 -i 14 0 -i 43 0 -i 10 0 -i 25 0 -i 26 0 -i 44 0 -i 45 0 -i 29 1')

    def timerEvent(self):
        self.showMute()
        if self.record or self.timeshift:
                if self.disc == 1:
                    Console().ePopen('fp_control -i 40 0')
                if self.disc == 2:
                    Console().ePopen('fp_control -i 39 0')
                if self.disc == 3:
                    Console().ePopen('fp_control -i 38 0 -i 40 1')
                if self.disc == 4:
                    Console().ePopen('fp_control -i 39 1')
                if self.disc == 5:
                    Console().ePopen('fp_control -i 38 1')
                self.disc += 1
                if self.disc == 6:
                    self.disc = 1
        if self.standby == False:
            next_rec_time = -1
            next_rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
            if next_rec_time > 0:
                Console().ePopen('fp_control -i 33 1')
            else:
                Console().ePopen('fp_control -i 33 0')

    def __evVideoSizeChanged(self):
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                height = info.getInfo(iServiceInformation.sVideoHeight)
                if height > 720:
                        Console().ePopen('fp_control -i 22 1')
                else:
                        Console().ePopen('fp_control -i 22 0')
                if height > 576:
                    Console().ePopen('fp_control -i 14 1')
                else:
                    Console().ePopen('fp_control -i 14 0')

    def __evSeekableStatusChanged(self):
            service = self.session.nav.getCurrentService()
            if service:
                if self.play == False:
                    ts = service and service.timeshift()
                    if ts and ts.isTimeshiftEnabled() > 0:
                        if ts and ts.isTimeshiftActive() > 0:
                            self.timeshift = True
                            Console().ePopen('fp_control -i 43 1')
                            self.discOn()
                        else:
                            self.timeshift = False
                            Console().ePopen('fp_control -i 43 0')
                            if self.record == False:
                                self.discOff()

    def gotRecordEvent(self, service, event):
            if event in (iRecordableService.evEnd, iRecordableService.evStart, None):
                recs = self.session.nav.getRecordings()
                nrecs = len(recs)
                if nrecs > 1:
                    self.record = True
                    Console().ePopen('fp_control -i 7 1 -i 15 1')
                elif nrecs > 0:
                    self.record = True
                    Console().ePopen('fp_control -i 7 1 -i 15 0')
                    self.discOn()
                else:
                    Console().ePopen('fp_control -i 7 0 -i 15 0 -i 33 0')
                    if self.timeshift == False:
                        self.discOff()
                    self.RecordEnd()
            return

    def RecordEnd(self):
        if self.record:
            self.record = False
            self.session.nav.record_event.remove(self.gotRecordEvent)

    def discOn(self):
            self.timer.stop()
            Console().ePopen('fp_control -i 40 1 -i 39 1 -i 38 1 -i 41 1')
            self.disc = 1
            self.timer.start(2000, False)

    def discOff(self):
            self.timer.stop()
            self.disc = 0
            Console().ePopen('fp_control -i 40 0 -i 39 0 -i 38 0 -i 41 0')
            self.timer.start(60000, False)

    def __evTunedIn(self):
        self.tuned = True
        Console().ePopen('fp_control -i 42 0 -i 37 0 -i 29 0')

    def __evTuneFailed(self):
        self.tuned = False

    def onLeaveStandby(self):
        self.standby = False
        self.timerEvent()
        Console().ePopen('fp_control -i 36 0 -l 0 0')
        if self.usb == 1:
                Console().ePopen('fp_control -i 13 1')
        else:
                Console().ePopen('fp_control -i 13 0')
        self.timer.start(60000, False)
        print '[VFD-Icons] set icons on Leave Standby'

    def onEnterStandby(self, configElement):
        from Screens.Standby import inStandby
        inStandby.onClose.append(self.onLeaveStandby)
        self.timer.stop()
        Console().ePopen('fp_control -i 46 0')
        self.standby = True
        Console().ePopen('fp_control -i 36 1')
        print '[VFD-Icons] set icons on Enter Standby'

    def hotplugCB(self, dev, media_state):
            if dev.__contains__('sda') or dev.__contains__('sdb'):
                if media_state == 'add' or media_state == 'change':
                    Console().ePopen('fp_control -i 13 1')
                    self.usb = 1
                if media_state == 'remove':
                    Console().ePopen('fp_control -i 13 0')
                    self.usb = 0


VFDIconsInstance = None

def main(session, **kwargs):
    global VFDIconsInstance
    if VFDIconsInstance is None:
        VFDIconsInstance = VFDIcons(session)
        VFDIconsInstance.UpdatedInfo()
    return


def Plugins(**kwargs):
    return [PluginDescriptor(name=_('VFD-Icons'), description=_('VFD-Icons for spark 7162'), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=main)]
