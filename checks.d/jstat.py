# -*- coding: utf-8 -*-
import commands
from checks import AgentCheck

class Jstat(AgentCheck):
    CONFS = {
              "S0C": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_0.current",
            "emission":        False
            },
              "S1C": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_1.current",
            "emission":        False
            },
              "S0U": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_0.used"
            },
              "S1U": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_1.used"
            },
              "S0F": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_0.free"
            },
              "S1F": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:survivor_1.free"
            },
              "EC": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:eden.current",
            "emission":        False
             },
              "EU": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:eden.used"
            },
              "EF": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:eden.free"
            },
              "OC": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:old.current",
            "emission":        False
            },
              "OU": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:old.used"
            },
              "OF": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:old.free"
            },
              "PC": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:permanent.current",
            "emission":        False
            },
              "PU": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:permanent.used"
            },
              "PF": {
            "metric":          "jstat.heap_memory",
            "additional_tag":  "heap_type:permanent.free"
            },
              "YGC": {
            "metric":          "jstat.gc.count",
            "additional_tag":  "gc_type:young"
            },
              "YGCT": {
            "metric":          "jstat.gc.time",
            "additional_tag":  "gc_type:young"
            },
              "FGC": {
            "metric":          "jstat.gc.count",
            "additional_tag":  "gc_type:full"
            },
              "FGCT": {
            "metric":          "jstat.gc.time",
            "additional_tag":  "gc_type:full"
            },
              "GCC": {
            "metric":          "jstat.gc.count",
            "additional_tag":  "gc_type:total",
            "emission":        False
            },
              "GCT": {
            "metric":          "jstat.gc.time",
            "additional_tag":  "gc_type:total",
            "emission":        False
            }
          }

    def check(self, instance):
        name = instance.get("name", None)
        tags = ('jvm_instance:%s' % name, ) + tuple(instance.get("tags", []))

        jstat = instance.get("jstat", "/usr/java/default/bin/jstat")

        pid = self._find_pid(instance)
        if pid is None:
            raise Exception('No pid found for %s. Please check your config yaml.' % name)

        values = map(lambda str: float(str), commands.getoutput('sudo %s -gc %s | tail -1' % (jstat, pid)).split())

        gc_names = ["S0C","S1C","S0U","S1U","EC","EU","OC","OU","PC","PU","YGC","YGCT","FGC","FGCT","GCT"]
        dic = dict(zip(gc_names, values))

        # Make heap metrics' unit byte
        heap_keys = filter(lambda str: "GC" not in str, gc_names)
        for key in heap_keys:
            dic[key] = dic[key] * 1024

        # calcurate free
        dic["S0F"] = dic["S0C"] - dic["S0U"]
        dic["S1F"] = dic["S1C"] - dic["S1U"]
        dic["EF"]  = dic["EC"]  - dic["EU"]
        dic["OF"]  = dic["OC"]  - dic["OU"]
        dic["PF"]  = dic["PC"]  - dic["PU"]
        dic["GCC"] = dic["YGC"] + dic["FGC"]

        for name, value in dic.iteritems():
            conf = self.CONFS[name]
            if conf.get("emission", True):
                self.gauge(conf["metric"], value, tags + (conf["additional_tag"], ))

    def _find_pid(self, instance):
        pid_filepath  = instance.get('pid_file', None)

        if pid_filepath is not None:
            return open(pid_filepath, "r").read().strip()

        search_regex = instance.get('search_regex', None)
        user          = instance.get('user', None)

        if search_regex is None:
            raise KeyError('"search_regex" is mandatory')

        return self._find_pid_by_search_regex(search_regex, user)


    def _find_pid_by_search_regex(self, search_regex, user):
        import psutil, re

        pattern = re.compile(search_regex)
        for proc in psutil.process_iter():
            cmdline = " ".join(proc.cmdline)
            if user is None or proc.username == user:
                if pattern.search(cmdline):
                    return proc.pid

        return None
