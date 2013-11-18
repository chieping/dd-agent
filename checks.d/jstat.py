import commands, re
from checks import AgentCheck

class Jstat(AgentCheck):

    def check(self, instance):
        tags = instance["tags"]
        service = instance["tomcat_service"]
        calculated_pid = re.compile(r"\(pid (\d+)\)").search(commands.getoutput("sudo /sbin/service %s status" % service)).group(1)

        values = map(lambda str: float(str), re.split(' +', commands.getoutput('sudo /usr/java/default/bin/jstat -gc %s | tail -1' % calculated_pid)))

        gc_names = ["S0C","S1C","S0U","S1U","EC","EU","OC","OU","PC","PU","YGC","YGCT","FGC","FGCT","GCT"]

        dic = dict(zip(gc_names, values))
        for key, val in dic.iteritems():
            self.gauge("jstat.%s" % key, val, tags)
