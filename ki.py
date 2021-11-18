#!/usr/bin/python3
#*************************************************
# Description : Kubectl Pro
# Version     : 0.2
#*************************************************
import os,re,sys,time,json,subprocess
#-----------------VAR-----------------------------
home = os.environ["HOME"]
ki_history = home + "/.ki_history"
ki_lock = ki_history + "/.lock"
ki_dict = ki_history + "/.dict"
ki_last = ki_history + "/.last"
ki_name = ki_history + "/.name"
default_config = home + "/.kube/config"
#-----------------FUN-----------------------------
def cmp_file(f1, f2):
    st1 = os.stat(f1)
    st2 = os.stat(f2)
    if st1.st_size != st2.st_size:
        return False
    bufsize = 8*1024
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True
def cmd_obj(ns, obj, res, args, iip="x"):
    if obj in ("node","no"):
        if args[0] == 'c':
            action = "cordon"
            cmd = "kubectl "+action+" "+res
        elif args[0] == 'u':
            action = "uncordon"
            cmd = "kubectl "+action+" "+res
        else:
            action = "ssh"
            cmd = action +" root@"+iip
    elif obj in ("event"):
        action = "get"
        cmd = "kubectl -n "+ns+" "+action+" "+obj+" --sort-by=.metadata.creationTimestamp"
    elif obj in ("deployment","deploy","service","svc","ingress","ing","configmap","cm","secret","persistentvolumes","pv","persistentvolumeclaims","pvc","statefulsets","sts"):
        action2 = ""
        if args == "cle":
            action = "delete"
        elif args[0] == "e":
            action = "edit"
        elif args[0] == 'o':
            action = "get"
            action2 = " -o yaml > "+res+"."+obj+".yml"
        elif args[0] == "d":
            action = "describe"
        else:
            action = "get"
        cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+res+action2
    else:
        obj = "pod"
        l = res.split('-')
        end = l[-1]
        if end.isdigit() and int(end) < 10000:
            del l[-1:]
            obj = "sts"
        else:
            del l[-2:]
        name = ('-').join(l)
        if args == "del":
            cmd = "kubectl -n "+ns+" delete pod "+res+" &"
        elif args == "cle":
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            action = "delete"
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+name
        elif args == "destory":
            action = "delete"
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            cmd = "kubectl -n "+ns+" "+action+" "+obj+",service,ingress "+name
        elif args[0] == "r":
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            cmd = "kubectl -n "+ns+" rollout restart "+obj+" "+name
        elif args[0] in ('o'):
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            action = "get"
            if len(args) > 1:
                if str(args)[1] == "d":
                    obj = "deploy"
                elif str(args)[1] == "s":
                    obj = "service"
                elif str(args)[1] == "i":
                    obj = "ingress"
                elif str(args)[1] == "f":
                    obj = "sts"
                else:
                    obj = "deploy"
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+name+" -o yaml > "+name+"."+obj+".yml"
        elif args[0] in ('d','e'):
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            action = "describe" if args[0] == 'd' else "edit"
            if len(args) > 1:
                if str(args)[1] == "d":
                    obj = "deploy"
                elif str(args)[1] == "s":
                    obj = "service"
                elif str(args)[1] == "i":
                    obj = "ingress"
                elif str(args)[1] == "f":
                    obj = "sts"
                elif str(args)[1] == "p":
                    obj = "pod"
                    name = res
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+name
        elif args[0] == 'c':
            obj = "sts" if end.isdigit() and int(end) < 10000 else "deploy"
            regular = args.split('c')[-1]
            action = "scale"
            replicas = regular if regular.isdigit() and -1 < int(regular) < 30 else str(1)
            cmd = "kubectl -n "+ns+" "+action+" --replicas="+replicas+" "+obj+"/"+name
        elif args[0] == 'l':
            regular = args.split('l')[-1]
            p = subprocess.Popen("kubectl -n "+ns+" get pod "+res+" -o jsonpath='{.spec.containers[:].name}'",shell=True,stdout=subprocess.PIPE,universal_newlines=True)
            result_list = p.stdout.readlines()[0].split()
            container = name if name in result_list else "--all-containers"
            if regular.isdigit():
                cmd = "kubectl -n "+ns+" logs -f "+res+" "+container+" --tail "+regular
            else:
                cmd = "kubectl -n "+ns+" logs -f "+res+" "+container+"|grep --color=auto "+regular if regular else "kubectl -n "+ns+" logs -f "+res+" "+container+" --tail 200"
        else:
            cmd = "kubectl -n "+ns+" exec -it "+res+" -- sh"
    return cmd
def find_ip(res: str):
    ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}',res)
    return ip[0] if ip else ""
def find_optimal(namespace_list: list, namespace: str):
    namespace_list.sort()
    indexes = [row.index(namespace) * 0.8 if namespace in row else 10000 for row in namespace_list]
    contains = [len(row.replace(namespace, '')) * 0.42 for row in namespace_list]
    words = [namespace == row for row in namespace_list]
    result_list = [(indexes[i] + container) * (1.62 if not words[i] else 1) for i, container in enumerate(contains)]
    return namespace_list[result_list.index(min(result_list))] if len(set(indexes)) != 1 else None
def find_config():
    os.path.exists(ki_history) or os.mkdir(ki_history)
    cmd = '''find $HOME/.kube -maxdepth 2 -type f -name 'kubeconfig*' 2>/dev/null|egrep '.*' || ( find $HOME/.kube -maxdepth 1 -type f 2>/dev/null|egrep '.*' &>/dev/null && grep -l "current-context" `find $HOME/.kube -maxdepth 1 -type f` )'''
    k8s_list = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    result_set = { e.split('\n')[0] for e in k8s_list.stdout.readlines() }
    result_num = len(result_set)
    result_lines = list(result_set)
    kubeconfig = None
    if result_num == 1:
        if os.path.exists(default_config):
            if not os.path.islink(default_config):
                with open(default_config,'r') as fr, open(home+"/.kube/config-0",'w') as fw: fw.write(fr.read())
                os.unlink(default_config)
                os.symlink(home+"/.kube/config-0",default_config)
                kubeconfig = "config-0"
            else:
                kubeconfig = result_lines[0].split("/")[-1]
        else:
            try:
                os.unlink(default_config)
            except:
                pass
            os.symlink(result_lines[0],default_config)
            kubeconfig = result_lines[0].split("/")[-1]
    elif result_num > 1:
        dc = {}
        if os.path.exists(ki_dict) and os.path.getsize(ki_dict) > 5:
            with open(ki_dict,'r') as f:
                try:
                    dc = json.loads(f.read())
                    for config in list(dc.keys()):
                        if not os.path.exists(config):
                            del dc[config]
                except:
                    os.remove(ki_dict)
        if os.path.exists(ki_last) and os.path.getsize(ki_last) > 0:
            with open(ki_last,'r') as f:
                last_config = f.read()
                if not os.path.exists(last_config):
                    last_config = result_lines[0]
        else:
            last_config = result_lines[0]
        result_dict = sorted(dc.items(),key = lambda dc:(dc[1], dc[0]),reverse=True)
        sort_list = [ i[0] for i in result_dict ]
        last_config in sort_list and sort_list.remove(last_config)
        sort_list.insert(0,last_config)
        result_lines = sort_list + list(result_set - set(sort_list))
        if os.path.exists(default_config):
            if not os.path.islink(default_config):
                with open(default_config,'r') as fr, open(home+"/.kube/config-0",'w') as fw: fw.write(fr.read())
                os.unlink(default_config)
                os.symlink(home+"/.kube/config-0",default_config)
                kubeconfig = "config-0"
            else:
                for e in result_lines:
                    if cmp_file(e,default_config): kubeconfig = e.strip().split("/")[-1]
        else:
            try:
                os.unlink(default_config)
            except:
                pass
            os.symlink(result_lines[0],default_config)
            kubeconfig = result_lines[0].split("/")[-1]
    return kubeconfig,result_lines,result_num
def find_history(config):
    dc = {}
    if os.path.exists(ki_dict) and os.path.getsize(ki_dict) > 5:
        with open(ki_dict,'r') as f:
            dc = json.loads(f.read())
            dc[config] = dc[config] + 1 if config in dc else 1
            dc.pop(default_config,404)
            for config in list(dc.keys()):
                if not os.path.exists(config): del dc[config]
    else:
        dc[config] = 1
    with open(ki_dict,'w') as f: f.write(json.dumps(dc))
def find_ns():
    l = find_config()
    ns = None
    kubeconfig = None
    switch = False
    result_num = l[-1]
    if result_num > 0:
        kn = sys.argv[2].split('.')
        ns_pattern = kn[-1] if len(kn) > 1 else kn[0]
        config = find_optimal(l[1],kn[0]) or default_config if len(kn) > 1 else default_config
        p1 = subprocess.Popen("kubectl get ns --no-headers --kubeconfig "+config,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        ns_set = list({ e.split()[0] for e in p1.stdout.readlines() })
        if ns_set:
            ns = find_optimal(ns_set,ns_pattern)
            os.path.realpath(config) in l[1] and l[1].remove(os.path.realpath(config))
            l[1].insert(0,config)
            for n,config in enumerate(l[1]):
                p1 = subprocess.Popen("kubectl get ns --no-headers --kubeconfig "+config,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                ns_set = list({ e.split()[0] for e in p1.stdout.readlines() })
                if ns_set:
                    ns = find_optimal(ns_set,ns_pattern)
                    if ns:
                        p2 = subprocess.Popen("kubectl get pods --no-headers --kubeconfig "+config+" -n "+ns,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                        if list({ e.split()[0] for e in p2.stdout.readlines() }):
                            if os.path.exists(default_config) and config not in {default_config,os.path.realpath(default_config)}:
                                if default_config != os.path.realpath(default_config):
                                    with open(ki_last,'w') as f: f.write(os.path.realpath(default_config))
                                os.unlink(default_config)
                                os.symlink(config,default_config)
                                l = find_config()
                                kubeconfig = config
                                print("\033[5;32m{}\033[0m".format("[ "+str(n+1)+" SWITCH  "+config.split("/")[-1]+" / "+ns+" ] "))
                                find_history(config)
                                switch = True
                            break
            kubeconfig = l[0]
    return ns,kubeconfig,switch,result_num
def info(k8s_path: str):
    l = k8s_path.split('/')
    if 'K8S' in l:
        if not os.path.exists(ki_lock) and len(l) > l.index('K8S')+1:
            k8s_str = l[l.index('K8S')+1].split('-')[0]
            result_lines = find_config()[1]
            if result_lines:
                config = find_optimal(result_lines,k8s_str)
                if config and os.path.exists(default_config) and config not in {default_config,os.path.realpath(default_config)}:
                    os.unlink(default_config)
                    os.symlink(config,default_config)
                    print("\033[1;35m{}\033[0m".format("[ "+config.split("/")[-1]+" (switch) ] "))
                else:
                    print("\033[1;36m{}\033[0m".format("[ "+os.path.realpath(default_config).split("/")[-1]+" ]"))
        else:
            print("\033[1;36m{}\033[0m".format("[ "+os.path.realpath(default_config).split("/")[-1]+(" (lock)" if os.path.exists(ki_lock) else "")+" ]"))
    else:
        print("\033[1;32m{}\033[0m".format("[ "+os.path.realpath(default_config).split("/")[-1]+" ]"))
        os.path.exists(ki_lock) and int(time.time()-os.stat(ki_lock).st_mtime) > 3600 and os.unlink(ki_lock)
def record(res: str,obj: str,cmd: str,kubeconfig: str):
    l = os.environ['SSH_CONNECTION'].split() if 'SSH_CONNECTION' in os.environ else ['NULL','NULL','NULL']
    USER = os.environ['USER'] if 'USER' in os.environ else "NULL"
    HOST = l[2]
    FROM = l[0]
    with open(ki_name,'w') as f:
        if obj == "pod":
            resList = res.split('-')
            last_res = ('-').join(resList[:-1]) if resList[-1].isdigit() and int(resList[-1]) < 10000 else ('-').join(resList[:-2])
        else:
            last_res = res
        f.write(last_res)
    ki_file = time.strftime("%F",time.localtime())
    with open(ki_history+"/"+ki_file,'a+') as f: f.write( time.strftime("%F %T ",time.localtime())+"[ "+USER+"@"+HOST+" from "+FROM+" ---> "+kubeconfig+" ]  " + cmd + "\n" )
def ki():
    ( len(sys.argv) == 1 or sys.argv[1] not in ('-n','-nr','-t','-t2','-s','-select','-l','-lock','-u','-unlock','-w','-watch','-h','-help') ) and sys.argv.insert(1,'-n')
    if len(sys.argv) == 2 and sys.argv[1] in ('-w','-watch'):
        info(os.environ["PWD"])
    elif len(sys.argv) == 2 and sys.argv[1] in ('-l','-lock'):
        os.path.exists(ki_history) or os.mkdir(ki_history)
        os.path.exists(ki_lock) or open(ki_lock,"a").close()
    elif len(sys.argv) == 2 and sys.argv[1] in ('-u','-unlock'):
        os.path.exists(ki_lock) and os.unlink(ki_lock)
    elif len(sys.argv) == 2 and sys.argv[1] == '-n':
        cmd = "kubectl get ns"
        print("\033[1;32m{}\033[0m".format(cmd))
        os.environ['KUBECONFIG'] = os.path.realpath(default_config)
        os.system(cmd)
    elif 1 < len(sys.argv) < 4 and sys.argv[1] in ('-s','-select'):
        result_lines = find_config()[1]
        if result_lines and len(result_lines) > 1:
            if len(sys.argv) == 3:
                config = find_optimal(result_lines,sys.argv[2])
                if config and os.path.exists(default_config) and config not in {default_config,os.path.realpath(default_config)}:
                    os.unlink(default_config)
                    os.symlink(config,default_config)
                    print("\033[1;32m{}\033[0m".format("[ SWITCH "+config.split("/")[-1]+" ] "))
            else:
                lr = set()
                for i in result_lines:
                    for j in result_lines:
                        if cmp_file(i,j) and i != j:
                            e = i if len(i) < len(j) else j
                            if e != default_config and e != os.path.realpath(default_config):
                                lr.add(e)
                for e in lr:
                    os.remove(e)
                    result_lines.remove(e)
                if os.path.exists(default_config):
                    pattern = ""
                    res = None
                    temp = result_lines
                    while True:
                        result_lines = list(filter(lambda x: x.find(pattern) >= 0, result_lines)) if pattern else temp
                        if result_lines:
                            for n,e in enumerate(result_lines):
                                if cmp_file(e,default_config):
                                    print("\033[5;32m{}\033[0m \033[1;32m{}\033[0m".format(n,e.strip()))
                                else:
                                    print("\033[1;32m{}\033[0m {}".format(n,e.strip()))
                            try:
                                pattern = input("\033[1;35m%s\033[0m\033[5;35m%s\033[0m" % ("select",":")).strip()
                            except:
                                sys.exit()
                            if pattern.isdigit() and 0 <= int(pattern) < len(result_lines) or len(result_lines) == 1:
                                index = int(pattern) if pattern.isdigit() else 0
                                res = (result_lines[index]).split()[0]
                            if res and res != default_config:
                                os.unlink(default_config)
                                os.symlink(res,default_config)
                                print("\033[5;32m{}\033[0m".format(res))
                                find_history(res)
                                open(ki_lock,"a").close()
                                break
                        else:
                            pattern = ""
                else:
                    print("\033[1;32m{}\033[0m\033[5;32m{}\033[0m".format("File not found ",default_config))
    elif 2 < len(sys.argv) < 5 and sys.argv[1] in ('-n','-nr','-t','-t2'):
        l = find_ns()
        ns = l[0]
        kubeconfig = l[1]
        switch = l[2]
        if ns:
            pod = ""
            obj = "pod"
            ext = " -o wide"
            if len(sys.argv) == 4:
                d = {'d':['deploy'," -o wide"],'s':['service'," -o wide"],'i':['ingress'," -o wide"],'c':['configmap'," -o wide"],'t':['secret'," -o wide"],'n':['node'," -o wide"],'p':['pvc'," -o wide"],'v':['pv'," -o wide"],'f':['sts'," -o wide"],'e':['event',''],'r':['rs','']}
                obj = d[sys.argv[3][0]][0] if sys.argv[3][0] in d else "pod"
                ext = d[sys.argv[3][0]][1] if sys.argv[3][0] in d else ""
            os.environ['KUBECONFIG'] = os.path.realpath(default_config)
            while True:
                if not pod:
                    if sys.argv[1] in ('-n','-nr'):
                        cmd = "kubectl "+("--sort-by=.status.containerStatuses[0].restartCount" if sys.argv[1].split('n')[-1] else "--sort-by=.metadata.creationTimestamp")+" get "+obj+ext+" --no-headers -n "+ ns
                    else:
                        cmd = "kubectl top "+obj+" --no-headers -n "+ ns +"|sort --key "+(sys.argv[1].split('t')[-1] or "3")+" --numeric"
                    print("\033[1;32m  {}\033[0m".format(cmd))
                    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                    result_lines = p.stdout.readlines()
                    if not result_lines:
                        break
                if not (pod.isdigit() and int(pod) < len(result_lines)):
                    result_lines = list(filter(lambda x: x.find(pod) >= 0, result_lines))
                if result_lines:
                    for n,e in enumerate(result_lines):
                        print("\033[1;32m{}\033[0m {}".format(n,e.strip()))
                    if n > 5:
                        style = "\033[5;32m{}\033[0m" if switch else "\033[1;32m{}\033[0m"
                        print(style.format("[ "+kubeconfig+" / "+ns+" --- "+obj.upper()+" ]"))
                        switch = False
                    try:
                        pod = input("\033[1;35m%s\033[0m\033[5;35m%s\033[0m" % ("select",":")).strip()
                        num = 10 + len(pod)
                    except:
                        sys.exit()
                    result_len = len(result_lines)
                    podList = pod.split()
                    pod = podList[0] if podList else ""
                    if pod in ('$','#','@','!'):
                        if pod == '$':
                            pod = str(result_len - 1)
                        elif os.path.exists(ki_name):
                            with open(ki_name,'r') as f:
                                last_res = f.read()
                                for n,e in enumerate(result_lines):
                                    if obj == "pod":
                                        resList = e.split()[0].split('-')
                                        res = ('-').join(resList[:-1]) if resList[-1].isdigit() and int(resList[-1]) < 10000 else ('-').join(resList[:-2])
                                    else:
                                        res = e.split()[0]
                                    if res == last_res:
                                        pod = str(n)
                                        break
                    args = ''.join(podList[1:]) if len(podList) > 1 else "p"
                    if pod.isdigit() and int(pod) < result_len or result_len == 1:
                        index = int(pod) if pod.isdigit() and int(pod) < result_len else 0
                        res = result_lines[index].split()[0]
                        iip = result_lines[index].split()[5] if len(result_lines[index].split()) > 5 else find_ip(res)
                        cmd = cmd_obj(ns,obj,res,args,iip)
                        record(res,obj,cmd,kubeconfig)
                        print('\033[{}C\033[1A'.format(num),end = '')
                        print("\033[1;32m{}\033[0m".format(cmd))
                        os.system(cmd)
                        print('\r')
                else:
                    pod = ""
        else:
            print("No namespace found in the kubernetes.")
    elif len(sys.argv) == 2 and sys.argv[1] in ('-h','-help'):
        style = "\033[1;32m%s\033[0m"
        print(style % "Kubectl Pro controls the Kubernetes cluster manager")
        print(style % "1. ki -s","Select the kubernetes to be connected ( if there are multiple ~/.kube/kubeconfig*,the kubeconfig storage can be kubeconfig-hz,kubeconfig-sh,etc. )")
        print(style % "2. ki $k8s.$ns","Select the kubernetes which namespace in the kubernetes ( if there are multiple ~/.kube/kubeconfig*,this way can be one-stop. )")
        print(style % "3. ki","List all namespaces")
        print(style % "4. ki xx","List all pods in the namespace ( if there are multiple ~/.kube/kubeconfig*,the best matching kubeconfig will be found ),the namespace parameter supports fuzzy matching,after outputting the pod list, select: xxx filters the query\n         select: index l ( [ l ] Print the logs for a container in a pod or specified resource )\n         select: index l 100 ( Print the logs of the latest 100 lines )\n         select: index l xxx ( Print the logs and filters the specified characters )\n         select: index r ( [ r ] Rollout restart the pod )\n         select: index o ( [ o ] Output the [Deployment,StatefulSet,Service,Ingress,Configmap,Secret].yml file )\n         select: index del ( [ del ] Delete the pod )\n         select: index cle ( [ cle ] Delete the Deployment/StatefulSet )\n         select: index e[si] ( [ e[si] ] Edit the Deploy/Service/Ingress )\n         select: index c5 ( [ c5 ] Set the Deploy/StatefulSet replicas=5 )")
        print(style % "5. ki xx d","List the Deployment of a namespace")
        print(style % "6. ki xx f","List the StatefulSet of a namespace")
        print(style % "7. ki xx s","List the Service of a namespace")
        print(style % "8. ki xx i","List the Ingress of a namespace")
        print(style % "9. ki xx t","List the Secret of a namespace")
        print(style % "10. ki xx v","List the PersistentVolume of a namespace")
        print(style % "11. ki xx p","List the PersistentVolumeClaim of a namespace")
def main():
    ki()
#-----------------PROG----------------------------
if __name__ == '__main__':
    main()
