#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
 Aptito 1.3
 Copyright (C) 2010
 Author: Mario Colque <mario@tuquito.org.ar>
 Tuquito Team! - www.tuquito.org.ar

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; version 3 of the License.
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.
 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
"""

import gtk
import os, commands, threading, gettext, apt
from time import sleep

gtk.gdk.threads_init()
from subprocess import Popen, PIPE

# i18n
gettext.install('aptito', '/usr/share/tuquito/locale')
flag = True

class Install(threading.Thread):
    def __init__(self, glade, flag=True):
        threading.Thread.__init__(self)
        self.glade = glade
        self.flag = flag
        self.pbar = self.glade.get_object('progressbar')
        os.chdir('/var/cache/apt/archives/')

    def setStatus(self, label):
        self.glade.get_object('status').set_markup('<i>' + label + '</i>')

    def cancelDownload(self, widget, data=None):
        self.comnd.kill()
        #os.system('killall -g axel')
        #os.system('killall -g apt-get')

    def noDownload(self):
        gtk.gdk.threads_enter()
        self.setStatus(_('Finished. No files for download'))
        self.glade.get_object('main-window').window.set_cursor(None)
        self.glade.get_object('packages').set_sensitive(True)
        self.glade.get_object('apply').set_sensitive(True)
        self.glade.get_object('cancel').set_sensitive(False)
        self.glade.get_object('check').set_sensitive(True)
        gtk.gdk.threads_leave()

    def run(self):
        global flag
        if self.flag:
            try:
                cache = apt.Cache()
                packagesList = []
                gtk.gdk.threads_enter()
                self.setStatus(_('Connecting...'))
                self.glade.get_object('main-window').window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                self.glade.get_object('cancel').connect('clicked', self.cancelDownload)
                self.glade.get_object('packages').set_sensitive(False)
                self.glade.get_object('apply').set_sensitive(False)
                self.glade.get_object('cancel').set_sensitive(True)
                self.glade.get_object('check').set_sensitive(False)
                self.glade.get_object('status').set_sensitive(True)
                gtk.gdk.threads_leave()

                check = self.glade.get_object('check').get_active()
                packages = self.glade.get_object('packages').get_text().strip().split(' ')

                for package in packages:
                    package = package.strip()
                    self.setStatus(_('Checking availability of ') + package + '...')
                    try:
                        pkg = cache[package]
                        if pkg.candidate.summary != '':
                            self.setStatus(_('Package found'))
                            if check:
                                if pkg.is_installed:
                                    self.setStatus(_('Package already installed, skipping ') + package + '...')
                                else:
                                    packagesList.append(package)
                            else:
                                packagesList.append(package)
                    except Exception, detail:
                        self.setStatus(_('The package does not exist'))

                if len(packagesList) > 0:
                    packagesList = ' '.join(packagesList)
                    cmd = 'apt-get --print-uris -y install %s | egrep -o -e "(ht|f)tp://[^\']+"' % packagesList
                    uris = commands.getoutput(cmd).split('\n')
                    cant = len(uris)
                    if cant > 0:
                        self.pbar.set_text(_('Connecting...'))
                        porc = round(float(100) / cant, 1)
                        porcent = 0.1
                        num = 0
                        for uri in uris:
                            if uri != '':
                                text = str(porcent) + '% - ' + str(num) + '/' + str(cant)
                                self.pbar.set_text(text)
                                self.setStatus(_('Downloading files...'))
                                cmd = 'axel -a ' + uri
                                self.comnd = Popen(cmd, shell=True)
                                returnCode = self.comnd.wait()
                                print self.comnd.pid
                                #os.system('axel -a ' + uri)
                                porcent = porcent + porc
                                num += 1
                        self.pbar.set_text('')
                        self.setStatus(_('Installing packages...'))
                        cmd = 'apt-get -y --force-yes install ' + packagesList
                        install = os.system(cmd)
                        if install != 0:
                            gtk.gdk.threads_enter()
                            self.setStatus(_('Error during process...'))
                            self.glade.get_object('packages').set_text(_('Error: Some packages causes conflicts during installation'))
                            self.glade.get_object('main-window').window.set_cursor(None)
                            self.glade.get_object('packages').set_sensitive(True)
                            self.glade.get_object('apply').set_sensitive(False)
                            self.glade.get_object('check').set_sensitive(False)
                            self.glade.get_object('status').set_sensitive(False)
                            gtk.gdk.threads_leave()
                        else:
                            gtk.gdk.threads_enter()
                            self.setStatus(_('The packages were successfully installed'))
                            self.glade.get_object('main-window').window.set_cursor(None)
                            self.glade.get_object('packages').set_sensitive(True)
                            self.glade.get_object('apply').set_sensitive(True)
                            self.glade.get_object('cancel').set_sensitive(False)
                            self.glade.get_object('check').set_sensitive(True)
                            gtk.gdk.threads_leave()
                    else:
                        self.noDownload()
                else:
                    self.noDownload()

            except Exception, detail:
                gtk.gdk.threads_enter()
                self.setStatus(_('Error during process...'))
                self.glade.get_object('packages').set_text(_('Error: ') + str(detail))
                self.glade.get_object('main-window').window.set_cursor(None)
                self.glade.get_object('packages').set_sensitive(True)
                self.glade.get_object('apply').set_sensitive(False)
                self.glade.get_object('cancel').set_sensitive(False)
                self.glade.get_object('check').set_sensitive(False)
                self.glade.get_object('status').set_sensitive(True)
                gtk.gdk.threads_leave()
            flag = False
        else:
            while flag:
                self.pbar.pulse()
                sleep(0.04)
            self.pbar.set_fraction(0.0)

class Aptito:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('/usr/lib/tuquito/aptito/aptito.glade')
        self.window = self.builder.get_object('main-window')

        self.packages_entry = self.builder.get_object('packages')
        self.builder.get_object('title').set_label('<big><b>' + _('Welcome to Aptito') + '</b></big>')
        self.builder.get_object('label-entry').set_label('%s <i>«%s»</i>' % (_('Enter the names of the packages to install separated by'), _('space')))
        self.builder.get_object('check').set_label(_('Skip updates'))
        self.builder.get_object('check').set_tooltip_text(_('If you enable this option, no updates were installed applications that are already installed. On the contrary, if not enabled, any application that is already installed will be updated in case of finding a new version.'))
        self.builder.connect_signals(self)
        self.window.show()

    def entryClean(self, widget, data=None, dat=None):
        self.packages_entry.set_text('')
        self.builder.get_object('apply').set_sensitive(True)
        self.builder.get_object('cancel').set_sensitive(False)
        self.builder.get_object('check').set_sensitive(True)
        self.builder.get_object('status').set_markup('')

    def quit(self, widget, data=None):
        gtk.main_quit()

    def install(self, widget, data=None):
        global flag
        packages = self.packages_entry.get_text().strip()
        if packages != '':
            flag = True
            install = Install(self.builder)
            install.start()
            install2 = Install(self.builder, False)
            install2.start()
        else:
            self.builder.get_object('status').set_label(_('Error: You must enter at least one package'))
            self.builder.get_object('status').set_sensitive(True)

if __name__ == '__main__':
    Aptito()
    gtk.main()
