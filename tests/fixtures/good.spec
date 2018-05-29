Name:           eject
Version:        1
Release:        1%{?dist}
Summary:        A test spec.

License:        Commercial
URL:            http://www.exmaple.org
Source0:        http://www.example.org/source.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)


%description
Just an example of specfile.

%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc



%changelog
