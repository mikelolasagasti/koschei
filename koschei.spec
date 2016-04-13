%bcond_without tests

Name:           koschei
Version:        1.5
Release:        2%{?dist}
Summary:        Continuous integration for Fedora packages
License:        GPLv2+
URL:            https://github.com/msimacek/%{name}
Source0:        https://github.com/msimacek/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  systemd

%if %{with tests}
BuildRequires:       python-nose
BuildRequires:       python-mock
BuildRequires:       python-sqlalchemy
BuildRequires:       koji
BuildRequires:       python-hawkey
BuildRequires:       python-librepo
BuildRequires:       rpm-python
BuildRequires:       fedmsg
BuildRequires:       python-psycopg2
BuildRequires:       postgresql-server
%endif

%description
Service tracking dependency changes in Fedora and rebuilding packages whose
dependencies change too much. It uses Koji scratch builds to do the rebuilds and
provides a web interface to the results.


%package common
Summary:        Acutual python code for koschei backend and frontend
Requires:       python-sqlalchemy
Requires:       python-psycopg2
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
Requires:       python-flask-openid
Requires:       python-flask-wtf
Requires:       python-jinja2
Requires:       mod_wsgi
Requires:       httpd

%description frontend
%{summary}.

%package backend
Summary:        Koschei backend services
Requires:       %{name}-common = %{version}-%{release}
Requires:       fedmsg
Requires:       koji
Requires:       python-dogpile-cache
Requires:       python-fedmsg-meta-fedora-infrastructure
Requires:       python-hawkey
Requires:       python-librepo
Requires:       rpm-python
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description backend
%{summary}.


%prep
%setup -q

sed 's|@CACHEDIR@|%{_localstatedir}/cache/%{name}|g
     s|@DATADIR@|%{_datadir}/%{name}|g
     s|@STATEDIR@|%{_sharedstatedir}/%{name}|g' config.cfg.template > config.cfg

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install --skip-build --root %{buildroot}

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d

cp -p empty_config.cfg %{buildroot}%{_sysconfdir}/%{name}/config.cfg
cp -p empty_admin_config.cfg %{buildroot}%{_sysconfdir}/%{name}/config-admin.cfg
cp -p config.cfg %{buildroot}%{_datadir}/koschei/

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

%if %{with tests}
%check
DB=$PWD/test/db
pg_ctl -s -w -D $DB init -o "-A trust"
pg_ctl -s -w -D $DB start -o "-F -h '' -k $DB"
TEST_WITH_POSTGRES=1 POSTGRES_HOST=$DB %{__python2} setup.py test
pg_ctl -s -w -D $DB stop -m immediate
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
%systemd_post %{name}-watcher.service
%systemd_post %{name}-polling.service
%systemd_post %{name}-resolver.service

%preun backend
%systemd_preun %{name}-scheduler.service
%systemd_preun %{name}-watcher.service
%systemd_preun %{name}-polling.service
%systemd_preun %{name}-resolver.service

%postun backend
%systemd_postun %{name}-scheduler.service
%systemd_postun %{name}-watcher.service
%systemd_postun %{name}-polling.service
%systemd_postun %{name}-resolver.service

%files common
%license LICENSE.txt
%{python2_sitelib}/*
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/config.cfg
%attr(755, %{name}, %{name}) %{_localstatedir}/cache/%{name}
%dir %{_sysconfdir}/%{name}
%attr(755, %{name}, %{name}) %dir %{_sharedstatedir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/config.cfg

%files admin
%{_bindir}/%{name}-admin
%{_datadir}/%{name}/alembic/
%{_datadir}/%{name}/alembic.ini
%config(noreplace) %{_sysconfdir}/%{name}/config-admin.cfg

%files frontend
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{_datadir}/%{name}/static
%{_datadir}/%{name}/templates
%{_datadir}/%{name}/%{name}.wsgi

%files backend
%{_libexecdir}/%{name}
%{_unitdir}/*

%changelog
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
