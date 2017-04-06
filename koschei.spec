%bcond_without tests
%global upstreamrel 1

Name:           koschei
Version:        1.10.0
Release:        1%{?dist}
Summary:        Continuous integration for Fedora packages
License:        GPLv2+
URL:            https://github.com/msimacek/%{name}
Source0:        https://github.com/msimacek/%{name}/archive/%{name}-%{version}-%{upstreamrel}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  systemd

%if %{with tests}
BuildRequires:       python-nose
BuildRequires:       python-vcrpy
BuildRequires:       python-mock
BuildRequires:       python-sqlalchemy
BuildRequires:       koji >= 1.11
BuildRequires:       python-hawkey
BuildRequires:       python-librepo
BuildRequires:       rpm-python
BuildRequires:       fedmsg
BuildRequires:       python-psycopg2
BuildRequires:       postgresql-server
BuildRequires:       python-flask
BuildRequires:       python-flask-sqlalchemy
BuildRequires:       python-flask-wtf
BuildRequires:       python-jinja2
BuildRequires:       python-dogpile-cache
BuildRequires:       python-six
BuildRequires:       python-copr >= 1.75
%endif

%description
Service tracking dependency changes in Fedora and rebuilding packages whose
dependencies change too much. It uses Koji scratch builds to do the rebuilds and
provides a web interface to the results.


%package common
Summary:        Acutual python code for koschei backend and frontend
Requires:       python-sqlalchemy
Requires:       python-psycopg2
Requires:       python-six
Requires:       rpm-python
Requires(pre):  shadow-utils
Obsoletes:      %{name} < 1.5.1

%description common
%{summary}.


%package admin
Summary:        Administration script and DB migrations for koschei
Requires:       %{name}-common = %{version}-%{release}
Requires:       python-alembic
Requires:       postgresql


%description admin
%{summary}.

%package frontend
Summary:        Web frontend for koschei using mod_wsgi
Requires:       %{name}-common = %{version}-%{release}
Requires:       python-flask
Requires:       python-flask-sqlalchemy
Requires:       python-flask-wtf
Requires:       python-jinja2
Requires:       mod_wsgi
Requires:       httpd
Requires:       js-jquery

%description frontend
%{summary}.

%package backend
Summary:        Koschei backend services
Requires:       %{name}-common = %{version}-%{release}
Requires:       koji
Requires:       python-hawkey
Requires:       python-librepo
Requires:       python-dogpile-cache
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description backend
%{summary}.

%package common-fedora
Summary:        Fedora-specific Koschei plugins (common parts of backend and frontend)
Requires:       %{name}-common = %{version}-%{release}
Requires:       python-dogpile-cache

%description common-fedora
%{summary}.

%package frontend-fedora
Summary:        Fedora-specific Koschei frontend plugins
Requires:       %{name}-frontend = %{version}-%{release}
Requires:       %{name}-common-fedora = %{version}-%{release}

%description frontend-fedora
%{summary}.

%package backend-fedora
Summary:        Fedora-specific Koschei backend plugins
Requires:       %{name}-backend = %{version}-%{release}
Requires:       %{name}-common-fedora = %{version}-%{release}
Requires:       fedmsg
Requires:       python-fedmsg-meta-fedora-infrastructure
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description backend-fedora
%{summary}.

%package common-copr
Summary:        Koschei plugin for user rebuilds in Copr (common part)
Requires:       %{name}-common = %{version}-%{release}

%description common-copr
%{summary}.

%package backend-copr
Summary:        Koschei plugin for user rebuilds in Copr (backend part)
Requires:       %{name}-backend = %{version}-%{release}
Requires:       %{name}-common-copr = %{version}-%{release}
Requires:       python-copr >= 1.75

%description backend-copr
%{summary}.

%package frontend-copr
Summary:        Koschei plugin for user rebuilds in Copr (frontend part)
Requires:       %{name}-frontend = %{version}-%{release}
Requires:       %{name}-common-copr = %{version}-%{release}

%description frontend-copr
%{summary}.


%prep
%setup -q -n %{name}-%{name}-%{version}-%{upstreamrel}

sed 's|@CACHEDIR@|%{_localstatedir}/cache/%{name}|g
     s|@DATADIR@|%{_datadir}/%{name}|g
     s|@VERSION@|%{version}|g
     s|@CONFDIR@|%{_sysconfdir}/koschei|g
     s|@STATEDIR@|%{_sharedstatedir}/%{name}|g' config.cfg.template > config.cfg

%build
%{__python2} setup.py build

aux/gen-bash-completion.py >koschei-admin.bash

%install
%{__python2} setup.py install --skip-build --root %{buildroot}

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d

cp -p config-backend.cfg %{buildroot}%{_sysconfdir}/%{name}/config-backend.cfg
cp -p config-frontend.cfg %{buildroot}%{_sysconfdir}/%{name}/config-frontend.cfg
cp -p config-admin.cfg %{buildroot}%{_sysconfdir}/%{name}/config-admin.cfg
cp -p config.cfg %{buildroot}%{_datadir}/koschei/
cp -p *.sql %{buildroot}%{_datadir}/koschei/

install -dm 755 %{buildroot}%{_unitdir}
for unit in systemd/*; do
    install -pm 644 $unit %{buildroot}%{_unitdir}/
done

install -pm 755 admin.py %{buildroot}%{_bindir}/%{name}-admin

install -dm 755 %{buildroot}%{_localstatedir}/cache/%{name}/repodata
install -dm 755 %{buildroot}%{_sharedstatedir}/%{name}

cp -pr templates %{buildroot}%{_datadir}/%{name}/

cp -pr alembic/ alembic.ini %{buildroot}%{_datadir}/%{name}/
cp -pr static %{buildroot}%{_datadir}/%{name}/
cp -p %{name}.wsgi %{buildroot}%{_datadir}/%{name}/
cp -p httpd.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf

install -dm 755 %{buildroot}%{_libexecdir}/%{name}
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-scheduler
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-watcher
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-polling
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-resolver
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-build-resolver
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-repo-resolver
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-copr-resolver
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/%{name}/koschei-copr-scheduler

install -dm 755 %{buildroot}%{_sysconfdir}/bash_completion.d/
install -p -m 644 koschei-admin.bash %{buildroot}%{_sysconfdir}/bash_completion.d/

%if %{with tests}
%check
. aux/set-env.sh
pg_init
pg_start
trap pg_stop 0
%{__python2} setup.py test
%endif

%pre common
getent group %{name} >/dev/null || groupadd -r %{name}
# services and koschei-admin script is supposed to be run as this user
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_localstatedir}/cache/%{name} -s /bin/sh \
    -c "Runs %{name} services" %{name}
exit 0

# Workaround for RPM bug #646523 - can't change symlink to directory
%pretrans frontend -p <lua>
dir = "%{_datadir}/%{name}/static"
dummy = posix.readlink(dir) and os.remove(dir)

%post backend
%systemd_post %{name}-scheduler.service
%systemd_post %{name}-polling.service
%systemd_post %{name}-resolver.service
%systemd_post %{name}-build-resolver.service
%systemd_post %{name}-repo-resolver.service

%preun backend
%systemd_preun %{name}-scheduler.service
%systemd_preun %{name}-polling.service
%systemd_preun %{name}-resolver.service
%systemd_preun %{name}-build-resolver.service
%systemd_preun %{name}-repo-resolver.service

%postun backend
%systemd_postun %{name}-scheduler.service
%systemd_postun %{name}-polling.service
%systemd_postun %{name}-resolver.service
%systemd_postun %{name}-build-resolver.service
%systemd_postun %{name}-repo-resolver.service

%post backend-fedora
%systemd_post %{name}-watcher.service

%preun backend-fedora
%systemd_preun %{name}-watcher.service

%postun backend-fedora
%systemd_postun %{name}-watcher.service

%post backend-copr
%systemd_post %{name}-copr-resolver.service
%systemd_post %{name}-copr-scheduler.service

%preun backend-copr
%systemd_preun %{name}-copr-resolver.service
%systemd_preun %{name}-copr-scheduler.service

%postun backend-copr
%systemd_postun %{name}-copr-resolver.service
%systemd_postun %{name}-copr-scheduler.service

%files common
%license LICENSE.txt
%{python2_sitelib}/*
%exclude %{python2_sitelib}/*/frontend
%exclude %{python2_sitelib}/*/backend
%exclude %{python2_sitelib}/*/plugins
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/config.cfg
%attr(755, %{name}, %{name}) %{_localstatedir}/cache/%{name}
%dir %{_sysconfdir}/%{name}
%attr(755, %{name}, %{name}) %dir %{_sharedstatedir}/%{name}

%files admin
%{_bindir}/%{name}-admin
%{_datadir}/%{name}/alembic/
%{_datadir}/%{name}/*.sql
%{_datadir}/%{name}/alembic.ini
%{_sysconfdir}/bash_completion.d
%config(noreplace) %{_sysconfdir}/%{name}/config-admin.cfg

%files frontend
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/%{name}/config-frontend.cfg
%{_datadir}/%{name}/static
%{_datadir}/%{name}/templates
%{_datadir}/%{name}/%{name}.wsgi
%{python2_sitelib}/*/frontend

%files backend
%config(noreplace) %{_sysconfdir}/%{name}/config-backend.cfg
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/koschei-scheduler
%{_libexecdir}/%{name}/koschei-polling
%{_libexecdir}/%{name}/koschei-resolver
%{_libexecdir}/%{name}/koschei-build-resolver
%{_libexecdir}/%{name}/koschei-repo-resolver
%{_unitdir}/koschei-scheduler.service
%{_unitdir}/koschei-polling.service
%{_unitdir}/koschei-resolver.service
%{_unitdir}/koschei-build-resolver.service
%{_unitdir}/koschei-repo-resolver.service
%{python2_sitelib}/*/backend
%{python2_sitelib}/*/plugins/repo_regen_plugin

%files common-fedora
%{python2_sitelib}/*/plugins/fedmsg_plugin
%{python2_sitelib}/*/plugins/pkgdb_plugin
%exclude %{python2_sitelib}/*/plugins/*/backend*
%exclude %{python2_sitelib}/*/plugins/*/frontend*

%files frontend-fedora
%{python2_sitelib}/*/plugins/pkgdb_plugin/frontend*

%files backend-fedora
%{_libexecdir}/%{name}/koschei-watcher
%{_unitdir}/koschei-watcher.service
%{python2_sitelib}/*/plugins/fedmsg_plugin/backend*
%{python2_sitelib}/*/plugins/pkgdb_plugin/backend*

%files common-copr
%{python2_sitelib}/*/plugins/copr_plugin
%exclude %{python2_sitelib}/*/plugins/*/backend*
%exclude %{python2_sitelib}/*/plugins/*/frontend*

%files frontend-copr
%{python2_sitelib}/*/plugins/copr_plugin/frontend*

%files backend-copr
%{_libexecdir}/%{name}/koschei-copr-resolver
%{_libexecdir}/%{name}/koschei-copr-scheduler
%{_unitdir}/koschei-copr-resolver.service
%{_unitdir}/koschei-copr-scheduler.service
%{python2_sitelib}/*/plugins/copr_plugin/backend*

%changelog
* Thu Apr 06 2017 Michael Simacek <msimacek@redhat.com> 1.10.0-1
- Update to upstream version 1.10.0

* Wed Mar 01 2017 Michael Simacek <msimacek@redhat.com> 1.9.1-1
- Update to upstream version 1.9.1

* Mon Feb 27 2017 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.9.0-2
- Fix requires on koschei-common-copr

* Thu Feb 23 2017 Michael Simacek <msimacek@redhat.com> 1.9.0-1
- Update to upstream version 1.9.0

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Sep 08 2016 Michael Simacek <msimacek@redhat.com> 1.8.2-1
- Update to upstream version 1.8.2

* Thu Sep 01 2016 Michael Simacek <msimacek@redhat.com> 1.8.1-1
- Update to upstream version 1.8.1

* Tue Aug 23 2016 Michael Simacek <msimacek@redhat.com> 1.8-1
- Update to upstream version 1.8

* Mon Aug 15 2016 Michael Simacek <msimacek@redhat.com> 1.7.2-1
- Update to upstream version 1.7.2

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.1-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Fri Jun 17 2016 Michael Simacek <msimacek@redhat.com> 1.7.1-1
- Update to upstream version 1.7.1

* Fri May 20 2016 Michael Simacek <msimacek@redhat.com> 1.7-1
- Update to upstream version 1.7

* Thu May 12 2016 Michael Simacek <msimacek@redhat.com> 1.6.1-1
- Fix registering real buids via watcher

* Thu Apr 21 2016 Michael Simacek <msimacek@redhat.com> 1.6-1
- Update to upstream release 1.6

* Fri Apr 08 2016 Michael Simacek <msimacek@redhat.com> 1.5-2
- Build with tito

* Thu Apr 07 2016 Michael Simacek <msimacek@redhat.com> - 1.5-1
- Update to upstream version 1.5

* Fri Mar 11 2016 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.3-1
- Update to upstream version 1.4.3

* Mon Mar  7 2016 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4.2-1
- Update to upstream version 1.4.2

* Wed Mar 02 2016 Michael Simacek <msimacek@redhat.com> - 1.4.1-1
- Update to upstream release 1.4.1

* Fri Feb 26 2016 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.4-1
- Update to upstream version 1.4

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Oct  2 2015 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.3-1
- Update to upstream version 1.3

* Wed Sep 23 2015 Michael Simacek <msimacek@redhat.com> - 1.2-2
- Backport fix for group editing permissions

* Tue Sep 22 2015 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.2-1
- Update to upstream version 1.2

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 02 2015 Michael Simacek <msimacek@redhat.com> - 1.1-1
- Update to version 1.1

* Wed May 20 2015 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.0-1
- Update to upstream version 1.0

* Fri Mar 27 2015 Mikolaj Izdebski <mizdebsk@redhat.com> - 0.2-2
- Add workaround for RPM bug #646523

* Thu Mar 12 2015 Michael Simacek <msimacek@redhat.com> - 0.2-1
- Update to version 0.2

* Mon Sep 01 2014 Michael Simacek <msimacek@redhat.com> - 0.1-2
- Fixed BR python-devel -> python2-devel
- Fixed changelog format
- Added noreplace to httpd config
- Replaced name occurences with macro

* Fri Jun 13 2014 Michael Simacek <msimacek@redhat.com> - 0.1-1
- Initial version
