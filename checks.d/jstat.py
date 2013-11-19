# -*- coding: utf-8 -*-
import commands, re
from checks import AgentCheck

class Jstat(AgentCheck):
    CONFS = [
              {
                "metric":          "heap.survivor.0",
                "additional_tag":  "jstat_state:current"
              },{
                "metric":          "heap.survivor.1",
                "additional_tag":  "jstat_state:current"
              },{
                "metric":          "heap.survivor.0",
                "additional_tag":  "jstat_state:used"
              },{
                "metric":          "heap.survivor.1",
                "additional_tag":  "jstat_state:used"
              },{
                "metric":          "heap.eden",
                "additional_tag":  "jstat_state:current"
              },{
                "metric":          "heap.eden",
                "additional_tag":  "jstat_state:used"
              },{
                "metric":          "heap.old",
                "additional_tag":  "jstat_state:current"
              },{
                "metric":          "heap.old",
                "additional_tag":  "jstat_state:used"
              },{
                "metric":          "heap.permanent",
                "additional_tag":  "jstat_state:current"
              },{
                "metric":          "heap.permanent",
                "additional_tag":  "jstat_state:used"
              },{
                "metric":          "gc.young.count"
              },{
                "metric":          "gc.young.time"
              },{
                "metric":          "gc.full.count"
              },{
                "metric":          "gc.full.time"
              },{
                "metric":          "gc.total.time"
              }
            ]

    def check(self, instance):

        # process.pyを見るとpsutilという外部ライブラリを使ってpidを取ってきたり
        # なんかしてるけど外部ライブラリの管理とかがよくわかっていないのでpsコマンドから
        # 取得します。

        tags = instance.get("tags", None)
        if tags is None:
            raise KeyError('The "tags" is mandatory')
        tags = tuple(tags)

        jstat = instance.get("jstat", "/usr/java/default/bin/jstat")

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

        for i, value in enumerate(values):
            conf = self.CONFS[i]
            additional_tag = conf.get("additional_tag", None)
            each_tags = tags + (additional_tag, ) if additional_tag is not None else tags
            self.gauge(conf["metric"], value, each_tags)
