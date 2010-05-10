#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
 Aptito 1.2
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

import gtk, pygtk
pygtk.require('2.0')
import os, commands, threading, gettext
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
		self.glade.get_object('status').set_label('<i>' + label + '</i>')
		
	def cancelDownload(self, widget, data=None):
		os.system('killall -g axel')
		os.system('killall -g apt-get')

	def run(self):
		global flag
		if self.flag:
			try:
				gtk.gdk.threads_enter()
				self.setStatus(_('Conectando...'))
				self.glade.get_object('main-window').window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
				self.glade.get_object('cancel').connect('clicked', self.cancelDownload)
				self.glade.get_object('packages').set_sensitive(False)
				self.glade.get_object('apply').set_sensitive(False)
				self.glade.get_object('cancel').set_sensitive(True)
				self.glade.get_object('check').set_sensitive(False)
				self.glade.get_object('status').set_sensitive(True)
				gtk.gdk.threads_leave()

				check = self.glade.get_object('check').get_active()
				packages = self.glade.get_object('packages').get_text().split(' ')
				packagesInstall = ''

				for package in packages:
					package = package.strip()
					self.setStatus(_('Verificando disponibilidad del paquete ') + package + '...')
					exists = commands.getoutput('apt-cache search ' + package + ' | cut -d " " -f1 | grep -x -m1 "' + package + '"')
					if exists != '':
						self.setStatus(_('Paquete encontrado'))
						if check:
							installed = commands.getoutput('dpkg --get-selections | grep install | cut -f1 | egrep -x "' + package + '"')
							if str(installed) == package:
								self.setStatus(_('Paquete ya instalado, omitiendo ') + package + '...')
							else:
								packagesInstall = packagesInstall + ' ' + package
						else:
							packagesInstall = packagesInstall + ' ' + package
					else:
						self.setStatus(_('No existe el paquete ') + package)

				packagesInstall = packagesInstall.strip()

				if packagesInstall != '':
					self.pbar.set_text(_('Conectando...'))
					cmd = 'apt-get --print-uris -y install ' + packagesInstall + ' | egrep -o -e "(ht|f)tp://[^\']+"'
					self.urls = commands.getoutput(cmd).split('\n')
					cant = len(self.urls)
					porc = round(float(100) / cant, 1)
					porcent = 0.1
					num = 0
					for url in self.urls:
						text = str(porcent) + '% - ' + str(num) + '/' + str(cant)
						self.pbar.set_text(text)
						self.setStatus(_('Descargando archivos...'))
						if url != '':
							os.system('axel -n6 -a ' + url)
						porcent = porcent + porc
						num += 1

					self.pbar.set_text('')
					self.setStatus(_('Instalando paquetes...'))
					cmd = 'apt-get -y --force-yes install ' + packagesInstall
					install = os.system(cmd)

					if install != 0:
						gtk.gdk.threads_enter()
						self.setStatus(_('Error durante los procesos...'))
						self.glade.get_object('packages').set_text(_('Error: Algun paquete ocasiona conflictos durante su instalacion'))
						self.glade.get_object('main-window').window.set_cursor(None)
						self.glade.get_object('packages').set_sensitive(True)
						self.glade.get_object('apply').set_sensitive(False)
						self.glade.get_object('check').set_sensitive(False)
						self.glade.get_object('status').set_sensitive(False)
						gtk.gdk.threads_leave()
					else:
						gtk.gdk.threads_enter()
						self.setStatus(_('Paquetes instalados correctamente'))
						self.glade.get_object('main-window').window.set_cursor(None)
						self.glade.get_object('packages').set_sensitive(True)
						self.glade.get_object('apply').set_sensitive(True)
						self.glade.get_object('cancel').set_sensitive(False)
						self.glade.get_object('check').set_sensitive(True)
						gtk.gdk.threads_leave()
				else:
					gtk.gdk.threads_enter()
					self.setStatus(_('Finalizado. Sin descargas por realizar'))
					self.glade.get_object('main-window').window.set_cursor(None)
					self.glade.get_object('packages').set_sensitive(True)
					self.glade.get_object('apply').set_sensitive(True)
					self.glade.get_object('cancel').set_sensitive(False)
					self.glade.get_object('check').set_sensitive(True)
					gtk.gdk.threads_leave()

			except Exception, detail:
				gtk.gdk.threads_enter()
				self.setStatus(_('Error durante los procesos...'))
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
		self.builder.get_object('title').set_label('<big><b>' + _('Bienvenido a Aptito') + '</b></big>')
		self.builder.get_object('label-entry').set_label(_('Ingrese los nombres de los paquetes a instalar separados por <i>«espacio»</i>'))
		self.builder.get_object('check').set_label(_('Omitir actualizaciones'))
		self.builder.get_object('check').set_tooltip_text(_('Si habilita esta opcion, no se instalaran actualizaciones de aplicaciones que ya se encuentren instaladas. Por el contrario, si no la habilita, toda aplicacion que ya se encuentre instalada se actualizara en caso de encontrar una nueva version.'))
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
			self.builder.get_object('status').set_label(_('Error: Debe ingresar al menos un paquete'))
			self.builder.get_object('status').set_sensitive(True)

if __name__ == '__main__':
	Aptito()
	gtk.main()