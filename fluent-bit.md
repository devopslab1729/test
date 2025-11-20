

fluent-bit.conf
```
#############################
# Fluent Bit — Single File
# Terraform Agent Log Router
#############################

##### SERVICE #####
[SERVICE]
    Flush        1
    Log_Level    info
    Daemon       off
    Parsers_File parsers.conf


##### INPUT: Custom Logs Written by Hooks #####
[INPUT]
    Name                tail
    Path                /var/log/tfc-agent/*.log
    Tag                 tf-agent.custom
    Parser              none
    Mem_Buf_Limit       10MB
    Skip_Long_Lines     On

##### FILTER: Kubernetes Metadata #####
[FILTER]
    Name        kubernetes
    Match       tf-agent.*
    Merge_Log   On

##### OUTPUT: Print to stdout (visible in kubectl logs) #####
[OUTPUT]
    Name        stdout
    Match       *
```


docker run
```
docker run -it -d --name fluent-bit  -v /root/fluet-bit:/fluent-bit/etc/  -v /root/tfc-agent-logs:/var/log/tfc-agent/ fluent/fluent-bit:4.0.13

```
cat agent-text.log
```
2025-11-20T12:00:00.000Z [INFO] agent: Starting Terraform agent v1.2.3
2025-11-20T12:00:01.500Z [INFO] agent: Connected to HCP Terraform
2025-11-20T12:00:05.123Z [INFO] agent: Handling run: id=run-abc123xyz, workspace=my-workspace
2025-11-20T12:00:10.789Z [INFO] terraform: Initializing provider plugins
2025-11-20T12:00:15.456Z [INFO] terraform: Applying changes
2025-11-20T12:00:20.901Z [INFO] agent: Run completed: id=run-abc123xyz, status=applied
2025-11-20T12:14:30.066Z [INFO] agent: Core update is available: v1.3.0

```


