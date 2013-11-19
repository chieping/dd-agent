import commands, re
from checks import AgentCheck

class Jstat(AgentCheck):

    def check(self, instance):
        gc_conf = self.init_config["gc"]
        self.log.info(gc_conf)
        tags = instance["tags"]
        service = instance["tomcat_service"]
        calculated_pid = re.compile(r"\(pid (\d+)\)").search(commands.getoutput("sudo /sbin/service %s status" % service)).group(1)

        values = map(lambda str: float(str), re.split(' +', commands.getoutput('sudo /usr/java/default/bin/jstat -gc %s | tail -1' % calculated_pid)))

        gc_names = ["S0C","S1C","S0U","S1U","EC","EU","OC","OU","PC","PU","YGC","YGCT","FGC","FGCT","GCT"]

        # dic = dict(zip(gc_names, values))
        # for key, val in dic.iteritems():
        #     self.gauge("jstat.%s" % key, val, tags)
        # dic = dict(zip(values, gc_conf))
        # for val, conf in dic.iteritems():
        #     tag = conf["tag"]
        #     self.log.info(tag)
        #     self.gauge(conf.metric, val, tags)

        for i, v in enumerate(values):
            conf = gc_conf[i]
            tag = conf.get("tag", None)
            each_tag = tuple(tags) + (conf["tag"],) if conf.has_key("tag") else tags
            self.log.info(each_tag)
            self.gauge(conf["metric"], v, each_tag)
