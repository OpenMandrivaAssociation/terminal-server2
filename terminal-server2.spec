%define name terminal-server2
%define rname terminal-server
%define version 1.5
%define release %mkrel 11
#client system root overlay for unionfs
%define sroot %{_localstatedir}/lib/%{rname}/common 
%define nroot %{_localstatedir}/lib/%{rname}/nfs
%define croot %{_localstatedir}/lib/%{rname}/clients

Summary: Terminal Server - Unionfs version
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{rname}-%{version}.tar.bz2
Source1: %{name}-extra-files.tar.bz2
Patch0: %{rname}-mdk-mods.patch
License: GPL
URL:	http://qa.mandriva.com/twiki/bin/view/Main/TerminalServer2
Group:	Networking/Other
BuildRoot: %{_tmppath}/%{name}-buildroot
Requires: nfs-utils tftp-server dhcp-server 
Requires: mkinitrd-net >= 1.10-26mdk
Requires: draktermserv usermode
Requires: etherboot usermode-consoleonly
Requires: unionfs-tools
Requires: desktop-common-data
Conflicts: terminal-server
BuildArch: noarch

%description
This package includes the files necessary in order to provide terminal
server functionality for diskless workstations on your network.

This version replaces clusternfs with unionfs over nfs.

There are security implications to installing this package.  
Specifically, it will make your entire filesystem accessible to any
station on the network.  Network stations will have the privilege level of
an anonymous user (via the all_squash nfs option), so this is not a major
security risk.  Network booting may not function correctly (or at all) if
certain key parts of your filesystem are not world-readable.

A configuration tool, draktermserv can be found in 
drakxtools.  Initially it is capable of setting up/start/stopping the server, 
creating etherboot floppy disks and isos, creating kernel net boot images for 
client machines, maintaining client user and machine lists, and configuring 
the dhcpd and clusternfs servers.

A fairly generic vesa xorg.conf is included for the client 
machines.

Basic cdrom/floppy mount points are also included, but you'll probably want 
to assign these per client machine.

This package is based on work by Michael Brown <mbrown@fensystems.co.uk>, 
with minor modifications for inclusion in Mandriva Linux.

See http://qa.mandriva.com/twiki/bin/view/Main/TerminalServer for
additional information.

%prep
%setup -q -n server-side
%patch -p1 -b .mdkTS

%build

%install
# (sb) relink now creates several bad symlinks - $$CLIENT$$ seems to confuse
export DONT_RELINK=1
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
mkdir -p $RPM_BUILD_ROOT%{croot}
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/sysconfig
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/X11
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/rc.d
mkdir -p $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc{2,3,5}.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/terminal-server/profiles
mkdir -p $RPM_BUILD_ROOT/sbin
mkdir -p $RPM_BUILD_ROOT%{sroot}/sbin
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_localstatedir}/lib
mkdir -p $RPM_BUILD_ROOT%{sroot}/mnt/cdrom
mkdir -p $RPM_BUILD_ROOT%{sroot}/mnt/floppy

# client files
install -m 644 inittab $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/inittab
install -m 644 fstab $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/fstab
install -m 644 network $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/sysconfig/network
ln -s /dev/null $RPM_BUILD_ROOT%{sroot}/.autofsck
touch $RPM_BUILD_ROOT%{sroot}/fastboot
ln -s /dev/null $RPM_BUILD_ROOT%{sroot}/sbin/depmod
ln -s /dev/null $RPM_BUILD_ROOT%{sroot}%{_sbindir}/fndSession
ln -s /dev/null $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/adjtime
ln -sf /tmp/issue $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/issue
ln -sf /tmp/issue.net $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/issue.net
ln -s /proc/mounts $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/mtab

cat > $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/modprobe.conf << EOF
install evdev /bin/true;
install tsdev /bin/true;
EOF

cat > $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/sysconfig/readonly-root << EOF
READONLY=yes
EOF

touch $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/modprobe.preload
touch $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/rc.readonly
ln -s /tmp/xorg.conf.test $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/X11/xorg.conf.test
ln -s /tmp $RPM_BUILD_ROOT%{sroot}%{_localstatedir}/lib/xkb
ln -s /tmp $RPM_BUILD_ROOT%{sroot}%{_localstatedir}/lib/gdm

# client init scripts
install -d $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/rc.d/init.d
cat > $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/rc.d/init.d/terminal-server << EOF
#!/bin/sh
# some misc terminal-server boot cleanups

# Source function library.
. /etc/rc.d/init.d/functions

# See how we were called.
case "\$1" in
  start)

    gprintf "Create/mount additional directories: "  
    [[ -d /var/run/console ]] || mkdir /var/run/console

    # remount client specific mount point rw
    UMOUNTS=\$(/usr/sbin/unionctl / --list | wc -l)
    if [ "\$UMOUNTS" = 3 ]; then
      /usr/sbin/unionctl / --mode rw /
    fi
   
    # seperate /home partititon
    HOMES=\$(ls /home)
    if [ -z "\$HOMES" ]; then
      gprintf "NFS mount /home: "
      SIP=\$(mount | grep 'type nfs' | head -1 | awk -F: '{print \$1}')
      mount -t nfs -o nolock,rsize=8192,wsize=8192 \$SIP:/home /home
    fi

    # only exists if nautilus is installed
    [[ -d /var/lib/gnome/desktop ]] && mount /var/lib/gnome/desktop
    echo
    ;;
  stop)
    gprintf "Nothing to do for stop: "
    echo
    ;;
  *)
    gprintf "*** Usage: terminal-server {start|stop}\n"
    exit 1
esac

exit 0
EOF

ln -sf ../init.d/udev $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc3.d/S01udev
ln -sf ../init.d/udev $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc5.d/S01udev
ln -sf ../init.d/xfs $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc5.d/S90xfs
ln -sf ../init.d/xfs $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc3.d/S90xfs
ln -sf ../init.d/terminal-server $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc5.d/S10terminal-server
ln -sf ../init.d/terminal-server $RPM_BUILD_ROOT%{nroot}%{_sysconfdir}/rc.d/rc3.d/S10terminal-server

# Default terminal-server profile
install -m 755 xterminal $RPM_BUILD_ROOT%{_sysconfdir}/terminal-server/profiles/xterminal

# General configuration files
install -m 644 dhcpd.conf.terminal-server.example $RPM_BUILD_ROOT%{_sysconfdir}/
install -m 644 exports $RPM_BUILD_ROOT%{_sysconfdir}/exports.terminal-server

# Utilities
install -m 755 mkdhcpdconf $RPM_BUILD_ROOT%{_sbindir}/

# Mandrakization + draktermserv
pushd $RPM_BUILD_ROOT
tar -xjf %{SOURCE1}
popd

chmod 0755 $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/rc.d/init.d/terminal-server

install -d $RPM_BUILD_ROOT%{_bindir}
ln -sf consolehelper $RPM_BUILD_ROOT%{_bindir}/draktermserv

# empty raidtab for client machines
touch $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/raidtab

# random-seed file
ln -s /tmp/random-seed $RPM_BUILD_ROOT%{sroot}%{_localstatedir}/lib/random-seed 

# installed but not packaged files
rm -f $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/X11/prefdm

# menu item for draktermserv, since it's not in mcc

mkdir -p $RPM_BUILD_ROOT%{_datadir}/applications
cat > $RPM_BUILD_ROOT%{_datadir}/applications/%{name}.desktop << EOF
[Desktop Entry]
Name=Terminal Server Administration
Comment=Setup/Administer Terminal Server and clients
Exec=/usr/sbin/draktermserv
Icon=other_configuration
Terminal=false
Type=Application
StartupNotify=true
Categories=X-MandrivaLinux-System-Configuration-Other;Settings;
EOF


# ensure root's ~/tmp directory gets made so drak tools work
mkdir -p $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/profile.d
cat > $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/profile.d/tmpdir.sh << EOF
#!/bin/sh
if [ -d \${HOME}/tmp -a -w \${HOME}/tmp ];then
    export TMPDIR=\${HOME}/tmp
    export TMP=\${HOME}/tmp
elif mkdir -p \${HOME}/tmp >/dev/null 2>&1;then
    chmod 700 \${HOME}/tmp
    export TMPDIR=\${HOME}/tmp
    export TMP=\${HOME}/tmp
else
    export TMPDIR=/tmp/
    export TMP=/tmp/
fi
EOF
chmod 0755 $RPM_BUILD_ROOT%{sroot}%{_sysconfdir}/profile.d/tmpdir.sh

%clean
rm -rf $RPM_BUILD_ROOT

%if %mdkversion < 200900
%post
%{update_menus}
%endif

%if %mdkversion < 200900
%postun
%{clean_menus}
%endif

%files
%defattr(-,root,root)
%dir %{_localstatedir}/lib/%{rname}
%dir %{sroot}
%dir %{sroot}%{_sysconfdir}
%dir %{sroot}%{_sysconfdir}/X11
%dir %{sroot}%{_sysconfdir}/X11/gdm
%dir %{sroot}%{_sysconfdir}/X11/xdm
%dir %{sroot}%{_sysconfdir}/profile.d
%dir %{sroot}%{_sysconfdir}/rc.d
%dir %{sroot}%{_sysconfdir}/rc.d/init.d
%dir %{nroot}
%dir %{nroot}%{_sysconfdir}
%dir %{nroot}%{_sysconfdir}/rc.d
%dir %{nroot}%{_sysconfdir}/rc.d/rc3.d
%dir %{nroot}%{_sysconfdir}/rc.d/rc5.d
%dir %{sroot}%{_sysconfdir}/sysconfig
%dir %{sroot}%{_var}
%dir %{sroot}%{_localstatedir}/lib
%dir %{sroot}%{_usr}
%dir %{sroot}%{_usr}/share
%dir %{sroot}%{_usr}/share/config
%dir %{sroot}%{_usr}/share/config/kdm
%dir %{sroot}%{_sbindir}
%dir %{sroot}/mnt
%dir %{sroot}/sbin
%dir %{croot}
%config(noreplace) %{sroot}%{_sysconfdir}/rc.d/init.d/terminal-server
%config(noreplace) %{sroot}%{_sysconfdir}/inittab
%config(noreplace) %{sroot}%{_sysconfdir}/fstab
%config(noreplace) %{sroot}%{_sysconfdir}/raidtab
%config(noreplace) %{_sysconfdir}/dhcpd.conf.pxe.include
%config(noreplace) %{sroot}%{_sysconfdir}/sysconfig/network
%config(noreplace) %{sroot}%{_sysconfdir}/sysconfig/readonly-root
%config(noreplace) %{sroot}%{_sysconfdir}/X11/gdm/gdm.conf
%config(noreplace) %{sroot}%{_sysconfdir}/X11/xdm/Xresources
%{sroot}%{_datadir}/config/kdm/kdmrc
%{sroot}/.autofsck
%{sroot}/fastboot
%{sroot}/sbin/depmod
%{sroot}%{_sbindir}/fndSession
%{sroot}%{_sysconfdir}/adjtime
%{sroot}%{_sysconfdir}/issue*
%{sroot}%{_sysconfdir}/modprobe*
%{sroot}%{_sysconfdir}/mtab
%{sroot}%{_sysconfdir}/rc.readonly
%{sroot}%{_sysconfdir}/profile.d/tmpdir.sh
%{sroot}%{_sysconfdir}/X11/xorg.conf.test
%config(noreplace) %{sroot}%{_sysconfdir}/X11/xorg.conf
%{sroot}%{_localstatedir}/lib/xkb
%{sroot}%{_localstatedir}/lib/gdm
%{sroot}%{_localstatedir}/lib/random-seed
%{nroot}%{_sysconfdir}/rc.d/rc3.d/S*
%{nroot}%{_sysconfdir}/rc.d/rc5.d/S*
%dir %{_sysconfdir}/terminal-server
%config(noreplace) %{_sysconfdir}/terminal-server/profiles/xterminal
%config(noreplace) %{_sysconfdir}/dhcpd.conf.terminal-server.example
%config(noreplace) %{_sysconfdir}/exports.terminal-server
%config(noreplace) %{_sysconfdir}/pam.d/draktermserv
%{_sbindir}/mkdhcpdconf
%_bindir/draktermserv
%{sroot}/mnt/cdrom
%{sroot}/mnt/floppy
%{_datadir}/applications/%{name}.desktop




%changelog
* Sat Aug 02 2008 Thierry Vignaud <tvignaud@mandriva.com> 1.5-11mdv2009.0
+ Revision: 261485
- rebuild

* Wed Jul 30 2008 Thierry Vignaud <tvignaud@mandriva.com> 1.5-10mdv2009.0
+ Revision: 254387
- rebuild
- drop old menu

  + Pixel <pixel@mandriva.com>
    - rpm filetriggers deprecates update_menus/update_scrollkeeper/update_mime_database/update_icon_cache/update_desktop_database/post_install_gconf_schemas
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Fri Dec 21 2007 Olivier Blin <oblin@mandriva.com> 1.5-8mdv2008.1
+ Revision: 136535
- restore BuildRoot

  + Thierry Vignaud <tvignaud@mandriva.com>
    - kill re-definition of %%buildroot on Pixel's request
    - kill explicit icon extension
    - kill desktop-file-validate's 'warning: key "Encoding" in group "Desktop Entry" is deprecated'


* Thu Jan 11 2007 Stew Benedict <sbenedict@mandriva.com> 1.5-8mdv2007.0
+ Revision: 107535
- Requires draktermserv now, not drakxtools

* Tue Jan 02 2007 Stew Benedict <sbenedict@mandriva.com> 1.5-7mdv2007.1
+ Revision: 103128
- Import terminal-server2

* Tue Jan 02 2007 Stew Benedict <sbenedict@mandriva.com> 1.5-7mdv2007.1
- drakTermServ -> draktermserv (#27835)

* Tue Aug 29 2006 Stew Benedict <sbenedict@mandriva.com> 1.5-6mdv2007.0
- better URL (Bug #24780)

* Fri Aug 25 2006 Stew Benedict <sbenedict@mandriva.com> 1.5-5mdv2007.0
- xdg menu

* Thu Mar 16 2006 Stew Benedict <sbenedict@mandriva.com> 1.5-4mdk
- add readonly-root
- update P0: update fstab with current cdrom,floppy syntax
  drop /proc from fstab - system rc.sysinit mounts it twice, 
  shows as [ FAILED ] in boot sequence

* Mon Mar 06 2006 Stew Benedict <sbenedict@mandriva.com> 1.5-3mdk
- update pam config

* Mon Dec 05 2005 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-2mdk
- Requires, update init script for unionfs issue

* Mon Dec 05 2005 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-1mdk
- first pass at new approach: unionfs over nfs

* Thu Mar 03 2005 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-24mdk
- misc mods to deal with changes in init scripts, packages
  * new fstab, some new $$CLIENT$$ symlinks
  * sync udev script
  * include dhcpd.conf.pxe.include
  * rename varrun init script to terminal-server and update

* Mon Dec 13 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-23mdk
- XF86Config-4 -> xorg.conf, Keyboard -> keyboard

* Mon Dec 13 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-22mdk
- more fstab entries

* Thu Dec 09 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-21mdk
- udev init script in runlevel 3,5
- remove /lib/dev-state from fstab$$CLIENT$$ (pixel)
- don't include shadow$$CLIENT$$, just causes confusion (pixel)

* Wed Sep 01 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-20mdk
- mirror udev initscript so we can write somewhere besides /dev.old
- replace forbidden name

* Sat Aug 21 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-19mdk
- removed devfsd requires, client link for /var/lib/random-seed

* Thu Mar 18 2004 David Baudens <baudens@mandrakesoft.com> 1.5-18mdk
- Fix menu (icon)

* Tue Feb 03 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-17mdk
- /lib/dev-state, /var/lib/gnome/desktop as tmpfs (Francisco Javier Felix)

* Mon Feb 02 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-16mdk
- /var/tmp as tmpfs (let KDE run)

* Thu Jan 29 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-15mdk
- more /var/lib/*dm mount points
- sync with current *dm config files
- create /var/run/console with client initscript
- /etc/qt_plugins_3.2* symlinks for clients to make mdkkdm happy

* Tue Jan 27 2004 Stew Benedict <sbenedict@mandrakesoft.com> 1.5-14mdk
- add /var/lib/gdm as tmpfs to fstab or gdm won't run

