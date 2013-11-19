# -*- coding: utf-8 -*-
import commands, re
from checks import AgentCheck

class Jstat(AgentCheck):
    CONFS = {
              "S0C": {
            "metric":          "heap.survivor.0",
            "additional_tag":  "jstat_state:current"
            },
              "S1C": {
            "metric":          "heap.survivor.1",
            "additional_tag":  "jstat_state:current"
            },
              "S0U": {
            "metric":          "heap.survivor.0",
            "additional_tag":  "jstat_state:used"
            },
              "S1U": {
            "metric":          "heap.survivor.1",
            "additional_tag":  "jstat_state:used"
            },
              "S0F": {
            "metric":          "heap.survivor.0",
            "additional_tag":  "jstat_state:free"
            },
              "S1F": {
            "metric":          "heap.survivor.1",
            "additional_tag":  "jstat_state:free"
            },
              "EC": {
            "metric":          "heap.eden",
            "additional_tag":  "jstat_state:current"
             },
              "EU": {
            "metric":          "heap.eden",
            "additional_tag":  "jstat_state:used"
            },
              "EF": {
            "metric":          "heap.eden",
            "additional_tag":  "jstat_state:free"
            },
              "OC": {
            "metric":          "heap.old",
            "additional_tag":  "jstat_state:current"
            },
              "OU": {
            "metric":          "heap.old",
            "additional_tag":  "jstat_state:used"
            },
              "OF": {
            "metric":          "heap.old",
            "additional_tag":  "jstat_state:free"
            },
              "PC": {
            "metric":          "heap.permanent",
            "additional_tag":  "jstat_state:current"
            },
              "PU": {
            "metric":          "heap.permanent",
            "additional_tag":  "jstat_state:used"
            },
              "PF": {
            "metric":          "heap.permanent",
            "additional_tag":  "jstat_state:free"
            },
              "YGC": {
            "metric":          "gc.young.count"
            },
              "YGCT": {
            "metric":          "gc.young.time"
            },
              "FGC": {
            "metric":          "gc.full.count"
            },
              "FGCT": {
            "metric":          "gc.full.time"
            },
              "GCT": {
            "metric":          "gc.total.time"
            }
          }

    def check(self, instance):
        tags = instance.get("tags", None)
        if tags is None:
            raise KeyError('The "tags" is mandatory')
        tags = tuple(tags)

        jstat = instance.get("jstat", "/usr/java/default/bin/jstat")

        # process.pyを見るとpsutilという外部ライブラリを使ってpidを取ってきたり
        # なんかしてるけど外部ライブラリの管理とかがよくわかっていないのでpsコマンドから
        # 取得します。
        search_string = instance.get('search_string', None)
        if search_string is None:
            raise KeyError('The "search_string" is mandatory')

        out = commands.getoutput('ps -ef | grep "%s" | grep -v grep' % search_string)
        pids = out.split("\n")
        if len(pids) is not 1:
            raise EnvironmentError("Searching result must include ONE pid. Actual had %d. SearchString: %s" % (len(pids), search_string))

        # PID is indexed second column
        calculated_pid = pids[0].split()[1]
        values = map(lambda str: float(str), commands.getoutput('sudo %s -gc %s | tail -1' % (jstat, calculated_pid)).split())

        gc_names = ["S0C","S1C","S0U","S1U","EC","EU","OC","OU","PC","PU","YGC","YGCT","FGC","FGCT","GCT"]
        dic = dict(zip(gc_names, values))

        # calcurate free
        dic["S0F"] = dic["S0C"] - dic["S0U"]
        dic["S1F"] = dic["S1C"] - dic["S1U"]
        dic["EF"]  = dic["EC"]  - dic["EU"]
        dic["OF"]  = dic["OC"]  - dic["OU"]
        dic["PF"]  = dic["PC"]  - dic["PU"]

        for name, value in dic.iteritems():
            conf = self.CONFS[name]
            additional_tag = conf.get("additional_tag", None)
            each_tags = tags + (additional_tag, ) if additional_tag is not None else tags
            self.gauge(conf["metric"], value, each_tags)
