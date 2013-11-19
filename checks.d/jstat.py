# -*- coding: utf-8 -*-
import commands, re
from checks import AgentCheck

class Jstat(AgentCheck):

    def check(self, instance):

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

        calculated_pid = pids[0].split()[1]

        gc_conf = self.init_config["gc"]
        tags = instance["tags"]

        values = map(lambda str: float(str), re.split(' +', commands.getoutput('sudo /usr/java/default/bin/jstat -gc %s | tail -1' % calculated_pid)))

        for i, v in enumerate(values):
            conf = gc_conf[i]
            tag = conf.get("tag", None)
            each_tag = tuple(tags) + (conf["tag"],) if conf.has_key("tag") else tags
            self.gauge(conf["metric"], v, each_tag)
