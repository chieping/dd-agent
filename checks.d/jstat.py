# -*- coding: utf-8 -*-
import commands, re
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
        tags = instance.get("tags", None)
        if tags is None:
            raise KeyError('The "tags" is mandatory')
        tags = tuple(tags)
        jstat = instance.get("jstat", "/usr/java/default/bin/jstat")
        search_string = instance.get('search_string', None)
        pid_filepath = instance.get('pid_file', None)
        if pid_filepath is None and search_string is None:
            raise KeyError('"pid_file" or "search_string" is mandatory')

        pid = self._find_pid_by_search_string(search_string) if pid_filepath is None else self._find_pid_by_pidfile(pid_filepath)
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
            additional_tag = conf.get("additional_tag", None)
            emission = conf.get("emission", True)
            each_tags = tags + (additional_tag, ) if additional_tag is not None else tags
            if emission:
                self.gauge(conf["metric"], value, each_tags)

    def _find_pid_by_pidfile(self, pid_filepath):
        # This function expects that file content is written only pid number.
        #
        # 現状だとtomcatのpidファイルのディレクトリ(temp)にRead権限がないため
        # (camptocamp/puppet-tomcatで設定される)Permission Denied と言われてしまう
        return open(pid_filepath, "r").read().strip()

    def _find_pid_by_search_string(self, search_string):
        # process.pyを見るとpsutilという外部ライブラリを使ってpidを取ってきたり
        # なんかしてるけど外部ライブラリの管理とかがよくわかっていないのでpsコマンドから
        # 取得します。
        out = commands.getoutput('ps -ef | grep "%s" | grep -v grep' % search_string)
        pids = out.split("\n")
        if len(pids) is not 1:
            raise EnvironmentError("Searching result must include ONE pid. Actual had %d. SearchString: %s" % (len(pids), search_string))
        # PID is indexed second column
        return pids[0].split()[1]
