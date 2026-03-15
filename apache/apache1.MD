Implementing a **production-ready Apache + Dispatcher + AEM dual cache architecture** requires several setup stages. Below is a **practical step-by-step implementation guide** used in real environments.

---

# 1. Architecture Prerequisites

Before starting, ensure you have:

| Component  | Example                      |
| ---------- | ---------------------------- |
| OS         | Ubuntu / RHEL                |
| Apache     | 2.4+                         |
| AEM        | AEM Author + Publish         |
| Dispatcher | Dispatcher module for Apache |
| Java       | JDK 11+                      |
| Network    | Load balancer / DNS          |

Example servers:

```text
Author Server
10.0.1.10

Publish Servers
10.0.1.20
10.0.1.21

Dispatcher (Apache)
10.0.1.30
10.0.1.31
```

---

# 2. Install Apache

Ubuntu example:

```bash
sudo apt update
sudo apt install apache2 -y
```

Enable modules:

```bash
sudo a2enmod cache
sudo a2enmod cache_disk
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod proxy
sudo a2enmod proxy_http
```

Restart Apache

```bash
sudo systemctl restart apache2
```

---

# 3. Install AEM Dispatcher Module

Download **Dispatcher module** from Adobe.

Example file:

```text
dispatcher-apache2.4-linux-x86_64.so
```

Copy module:

```bash
sudo cp dispatcher-apache2.4-linux-x86_64.so /usr/lib/apache2/modules/mod_dispatcher.so
```

Enable module:

```apache
LoadModule dispatcher_module modules/mod_dispatcher.so
```

Restart Apache:

```bash
sudo systemctl restart apache2
```

---

# 4. Create Cache Directories

Layer 1 Apache cache:

```bash
sudo mkdir -p /opt/apache/cache
sudo chown -R www-data:www-data /opt/apache/cache
```

Layer 2 Dispatcher cache:

```bash
sudo mkdir -p /opt/apache/html
sudo chown -R www-data:www-data /opt/apache/html
```

---

# 5. Configure Apache mod_cache (Layer 1)

Edit:

```text
/etc/apache2/sites-available/vhost.conf
```

Add:

```apache
CacheRoot "/opt/apache/cache"
CacheDirLevels 1
CacheDirLength 2

CacheDefaultExpire 3600

CacheEnable disk /is/image/
CacheEnable disk /product/
CacheEnable disk /produit/

CacheIgnoreNoLastMod On
CacheIgnoreCacheControl On
CacheIgnoreQueryString Off

CacheIgnoreHeaders Set-Cookie Cookie Pragma Expires Vary
```

---

# 6. Configure Dispatcher in Apache

Add inside VirtualHost.

```apache
<IfModule disp_apache2.c>

DispatcherConfig /etc/apache2/conf/dispatcher.any
DispatcherLog /var/log/apache2/dispatcher.log
DispatcherLogLevel 3

DispatcherUseProcessedURL 1
DispatcherPassError 0

</IfModule>
```

---

# 7. Create dispatcher.any Configuration

File:

```text
/etc/apache2/conf/dispatcher.any
```

Basic example:

```apache
/farms
{
  /website
  {
    /renders
    {
      /publish1
      {
        /hostname "10.0.1.20"
        /port "4503"
      }

      /publish2
      {
        /hostname "10.0.1.21"
        /port "4503"
      }
    }

    /cache
    {
      /docroot "/opt/apache/html"

      /rules
      {
        /0000 { /glob "*" /type "allow" }
      }

      /invalidate
      {
        /0000 { /glob "*" /type "deny" }
        /0001 { /glob "*.html" /type "allow" }
      }

      /enableTTL "1"
    }
  }
}
```

---

# 8. Configure Apache Virtual Host

File:

```text
/etc/apache2/sites-available/aem-site.conf
```

Example:

```apache
<VirtualHost *:80>

ServerName www.site.com
DocumentRoot /opt/apache/html

<Directory />
    AllowOverride None
    Require all denied
</Directory>

<Directory "/opt/apache/html">
    AllowOverride None
    Require all granted
</Directory>

DispatcherUseProcessedURL 1
DispatcherPassError 0

</VirtualHost>
```

Enable site:

```bash
sudo a2ensite aem-site.conf
sudo systemctl reload apache2
```

---

# 9. Configure Dispatcher Flush Agent (AEM)

In **AEM Author**:

Go to

```text
Tools → Deployment → Replication
```

Create:

```text
Dispatcher Flush Agent
```

Settings:

| Field         | Value                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------ |
| Transport URI | [http://dispatcher-server/dispatcher/invalidate.cache](http://dispatcher-server/dispatcher/invalidate.cache) |
| User          | dispatcher                                                                                                   |
| Password      | dispatcher                                                                                                   |

This ensures **cache invalidation when publishing**.

---

# 10. Test the Setup

Restart Apache.

```bash
sudo systemctl restart apache2
```

Test page:

```bash
curl -I http://www.site.com/content/site/en.html
```

Check cache directory:

```bash
ls /opt/apache/html
```

Check Apache cache:

```bash
ls /opt/apache/cache
```

---

# 11. Verify Cache Hits

Enable response headers.

Add in Apache:

```apache
Header add X-Cache-Status %{CACHE_STATUS}e env=CACHE_STATUS
```

Test:

```bash
curl -I http://www.site.com/page.html
```

Example output:

```text
X-Cache-Status: HIT
```

---

# 12. Production Best Practices

### Enable Security Filters

Block dangerous paths.

Example:

```apache
/filter
{
 /0001 { /type "deny" /glob "/system/*" }
}
```

---

### Enable Gzip

```apache
a2enmod deflate
```

---

### Enable HTTPS

Use **Let's Encrypt** or corporate certificate.

---

### Log Monitoring

Logs:

```text
/var/log/apache2/access.log
/var/log/apache2/error.log
/var/log/apache2/dispatcher.log
```

---

# Final Request Flow

```text
Browser
   │
CDN
   │
Load Balancer
   │
Apache mod_cache
   │
Dispatcher Cache
   │
AEM Publish
```

---

✅ After implementation you should see **90%+ cache hit ratio**, which dramatically reduces **AEM load and response time**.

---

If you'd like, I can also show **a full production-ready AEM Dispatcher project structure (Git repo layout used in CI/CD)** that companies use to deploy Apache + Dispatcher configurations automatically.
