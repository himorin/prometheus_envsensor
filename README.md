# prometheus_envsensor - Envionment sensor exporter

In personal use.


## design

### external connection

HTTP server based on http.server, and handles only following paths:

* `/metrics` standard prometheus format
* `/config.json` system configuration parameter

any other requests will get static HTML page stored in resource directory. 

Each request to `/metrics` will trigger to update internal cache of values 
and cached values are returned to requests, 
but no new update to cache is made within certain time from previous update 
(like 30s, by configuration) to reduce sensor reading. 

### sensor handling

Sensors are connected to its host with following structure:

```
Host (exporter: "IP", "port")
 +-- Sensor module 1 (python class: "modname", "sid")
 |    +-- Measured value A (defined by sensor module: "label", "TYPE", "HELP")
 |    |    +-- value ID 1 (for multiple sensors: "vid")
 |    |    +-- ...
 |    +-- Measured value B
 |    +-- ...
 +-- Sensor module 2
 +-- ...
```

Used names (labelled with `"xx"`) are as follows:

* `"IP"`: IP address of host running node
* `"port"`: port number of node listening
* `"modname"`: module name, mapping to Python class name is defined separatedly
* `"sid"`: Sensor ID, convention to bus etc. are defined by module
* `"label"`: label for metrics name, defined by module
* `"TYPE"`: used for metrics as `# TYPE` line, defined by module
* `"HELP"`: used for metrics as `# HELP` line, defined by module
* `"vid"`: ID of measured value, if module supports multiple in the same label

#### metrics label

For each set of `modname` and `sid`, following items are listd into metrics:

* `envsensor_success{modname, sid}`: 0/1, succeeded to access/read sensor module
* `envsensor_<modname>_<label>{sid, vid}`: value supplied from module

Note, at data acquisition and storing server, 
each data set are distinguished by IP address and port number of instance.
Final data element will be listed like: 
`envsensor_AHT10_temperature{AHT10="A",instance="mgmt",job="environment",port="9901",services="environment"}`

In `/metrics` page, each group of lines will have heading `# HELP` and `# TYPE` 
lines to be used by data storing server.

#### Sensor module interface

Each python class shall have following interfaces:

* `initialize(hash)`: 
  initialize a module with configuration options, 
  data in hash is defined by each module
* `read()`:
  read all sensor values, and return array of hash for values (by "value")
* `list()`:
  return array of hash for HELP and TYPE (by "HELP" and "TYPE")

Array of hash returned from interfaces are:
`[ {"label": "<label>", "vid": "<vid>", "value": "<value>", ...}, {} ... ]` 
where items after "value" are data to be returned. 

Interfaces are called as:

* immediately after instance is made, `initialize(hash)` is called
* after initialized, `list()` is called to get list of sensing data
  (assuming not to be changed over exporter is working)
* `read()` will be called upon external request

### Internal design

Four global data: hash for module instance, array for cache, 
hash for registration, `last-query`

#### Data cache

Following calls of `list()`, one hash for registration and one array for cache 
are built.

* Array for cache is an array of hash, as (cid = cache ID, starts from 0):
  `data[cid] = {"<modname>", "<label>", "<sid>", "<vid>", "<value>", "<HELP>", "<TYPE>", "last": "(last-modified)"}`.
* Hash for registration is tree of sensors, as (cid is ID defined above):
  `hash["<modname>"]["<label>"]["<sid>"]["<vid>"] = <cid>`

`"<xxx>"` are ones defined above, and stored into hash as label with xxx.
`"<value>"` and `"last"` are initialized as 0. 

Following calls of `read()`, `"<value>"` and `"last"` are updated. 
`"last"` is time (`time.time()`) of data update, 
the same over one series of update or taken per each `read()` call is 
undefined - will not make difference. 
On this update, `last-query` is updated with the time of finished. 

#### Per each external calls

First, check `last-query` and just return cache when `last-query` is closer 
than configured cache living time (default to 30s).

If not, call `read()` over all modules and update cache.
Then return cache.


### configuration

Configuration are stored in json file.

* `server_name`: (no formal use) could be presented at non-`/metrics` page
  (default to "Environment sensor exporter")
* `port`: port number to listen (default to 9902)
* `cache`: cache living time in sec (default to 30)
* `modules` (array of following hash)
  * `name`: name of module to be loaded (python class name convention will be listed separatedly)
  * `sid`: sensor ID, unique within each name of sensor
  + `conf`: hash of configuration parameter, directly passed to `initialize()`

