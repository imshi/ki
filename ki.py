#!/usr/bin/python3
#*************************************************
# Description : ki.py for kubectl
# Version     : 0.1
#*************************************************
import os,re,sys,subprocess
#-----------------VAR-----------------------------
#-----------------CLS-----------------------------
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
def cmd_obj(ns,obj,res,args,iip="x"):
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
        if args[0] == 'e':
            action = "edit"
        elif args[0] == 'd':
            action = "describe"
        elif args[0] == 'o':
            action = "get"
            action2 = " -o yaml > "+res+"."+obj+".yml"
        elif args == 'cle':
            action = "delete"
        else:
            action = "get"
        cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+res+action2
    else:
        obj = "pod"
        l = res.split('-')
        end = l[-1]
        if end.isdigit():
            del l[-1:]
            obj = "sts"
        else:
            del l[-2:]
        name = ('-').join(l)
        if args == "del":
            cmd = "kubectl -n "+ns+" delete pod "+res+" &"
        elif args == "cle":
            obj = "sts" if end.isdigit() else "deploy"
            res2 = name
            action = "delete"
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+res2
        elif args[0] == "r":
            obj = "sts" if end.isdigit() else "deploy"
            cmd = "kubectl -n "+ns+" rollout restart "+obj+" "+name
        elif args[0] in ('o'):
            obj = "sts" if end.isdigit() else "deploy"
            res2 = name
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
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+res2+" -o yaml > "+res2+"."+obj+".yml"
        elif args[0] in ('d','e'):
            obj = "sts" if end.isdigit() else "deploy"
            res2 = name
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
                    res2 = res
            cmd = "kubectl -n "+ns+" "+action+" "+obj+" "+res2
        elif args[0] == 'l':
            regular = args.split('l')[-1]
            p = subprocess.Popen("kubectl -n "+ns+" get pod "+res+" -o jsonpath='{.spec.containers[:].name}'",shell=True,stdout=subprocess.PIPE,universal_newlines=True)
            result_list = p.stdout.readlines()[0].split()
            if name in result_list:
                if regular.isdigit():
                    cmd = "kubectl -n "+ns+" logs -f "+res+" "+name+" --tail "+regular
                else:
                    cmd = "kubectl -n "+ns+" logs -f "+res+" "+name+"|grep --color=auto "+regular if regular else "kubectl -n "+ns+" logs -f "+res+" "+name+" --tail 200"
            else:
                if regular.isdigit():
                    cmd = "kubectl -n "+ns+" logs -f "+res+" --all-containers --tail "+regular
                else:
                    cmd = "kubectl -n "+ns+" logs -f "+res+" --all-containers |grep --color=auto "+regular if regular else "kubectl -n "+ns+" logs -f "+res+" --all-containers --tail 200"
        else:
            cmd = "kubectl -n "+ns+" exec -it  "+res+"  -- sh"
    return cmd
def find_optimal(namespace_list: list, namespace: str):
    indexes = [row.index(namespace) * 0.8 if namespace in row else 10000 for row in namespace_list]  # 按下标位置取最小权重
    contains = [len(row.replace(namespace, '')) * 0.42 for row in namespace_list]  # 取包含字符量最小权重
    words = [re.compile(f"\\b{namespace}\\b", re.I).search(row) is not None for row in namespace_list]  # 按单词配置权重
    result_list = [(indexes[i] + container) * (1.62 if not words[i] else 1) for i, container in enumerate(contains)]  # 权重组合
    return namespace_list[result_list.index(min(result_list))] if len(set(indexes)) != 1 else None
def find_config():
    cmd = "find $HOME/.kube -maxdepth 2 -type f -name 'kubeconfig*'"
    k8s_list = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    result_lines = list({ e.split('\n')[0] for e in k8s_list.stdout.readlines() })
    result_lines.sort()
    dst = os.environ.get("HOME")+"/.kube/config"
    kubeconfig = None
    if result_lines:
        if os.path.exists(dst):
            for n,e in enumerate(result_lines):
                if cmp_file(e,dst):
                    kubeconfig = e.strip().split("/")[-1]
        else:
            with open(dst,'w') as f:
                fi = open(result_lines[0])
                f.write(fi.read())
                fi.close()
            kubeconfig = result_lines[0].split("/")[-1]
    else:
        if os.path.exists(dst):
            with open(os.environ.get("HOME")+"/.kube/kubeconfig",'w') as f:
                fi = open(dst)
                f.write(fi.read())
                fi.close()
            kubeconfig = "kubeconfig"
        else:
            kubeconfig = None
    k8s_list = subprocess.Popen("find $HOME/.kube -maxdepth 2 -type f -name 'kubeconfig*'",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    result_num = len(list({ e.split('\n')[0] for e in k8s_list.stdout.readlines() }))
    return kubeconfig,result_lines,result_num
def find_ns():
    l = find_config()
    result_num = l[-1]
    if result_num > 0:
        p1 = subprocess.Popen("kubectl get ns --no-headers",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        ns_set = list({ e.split()[0] for e in p1.stdout.readlines() })
        ns = find_optimal(ns_set,sys.argv[2])
        flag = True
        if ns:
            p2 = subprocess.Popen("kubectl get pods --no-headers -n "+ns,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
            if list({ e.split()[0] for e in p2.stdout.readlines() }):
                flag = False
                pass
        if flag and result_num > 1:
            l[1].remove(os.environ.get("HOME")+"/.kube/"+l[0])
            for config in l[1]:
                p1 = subprocess.Popen("kubectl get ns --no-headers --kubeconfig "+config,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                ns_set = list({ e.split()[0] for e in p1.stdout.readlines() })
                ns = find_optimal(ns_set,sys.argv[2])
                if ns:
                    p2 = subprocess.Popen("kubectl get pods --no-headers --kubeconfig "+config+" -n "+ns,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                    if list({ e.split()[0] for e in p2.stdout.readlines() }):
                        dst = os.environ.get("HOME")+"/.kube/config"
                        if os.path.exists(dst):
                            os.unlink(dst)
                            os.symlink(config,dst)
                            l = find_config()
                            print("\033[5;32;40m%s\033[0m"%("[ switch to "+config.split("/")[-1]+" / "+ns+" ]"))
                            break
        kubeconfig = l[0]
    else:
        ns = None
        kubeconfig = None
    return ns,kubeconfig,result_num
def ki():
    if sys.argv[1] == '-s' and len(sys.argv) == 2:
        result_lines = find_config()[1]
        if result_lines and len(result_lines) > 1:
            lr = set()
            for i in result_lines:
                for j in result_lines:
                    if cmp_file(i,j) and i != j:
                        e = i if len(i) < len(j) else j
                        lr.add(e)
            for e in lr:
                os.remove(e)
                result_lines.remove(e)
            dst = os.environ.get("HOME")+"/.kube/config"
            if os.path.exists(dst):
                k8s = ""
                res = None
                temp = result_lines
                while True:
                    if k8s:
                        k8s = str(k8s)
                    else:
                        result_lines = temp
                    result_lines = list(filter(lambda x: x.find(k8s) >= 0, result_lines))
                    if result_lines:
                        for n,e in enumerate(result_lines):
                            if cmp_file(e,dst):
                                print("\033[5;32;40m%s\033[0m"%n,e.strip())
                            else:
                                print("\033[1;32;40m%s\033[0m"%n,e.strip())
                        try:
                            k8s = input("\033[1;32;35m%s\033[0m\033[5;32;35m%s\033[0m" % ("select",":"))
                            k8s = k8s.strip()
                        except:
                            sys.exit()
                        if k8s.isdigit() and 0 <= int(k8s) < len(result_lines) or len(result_lines) == 1:
                            index = int(k8s) if k8s.isdigit() else 0
                            res = (result_lines[index]).split()[0]
                        if res:
                            os.unlink(dst)
                            os.symlink(res,dst)
                            print("\033[1;32;40m%s\033[0m" % res)
                            break
                    else:
                        k8s = ""
            else:
                print("\033[1;32;35m%s\033[0m\033[5;32;35m%s\033[0m " % ("File not found ",dst))
    elif sys.argv[1] == '-n' and len(sys.argv) == 2:
        cmd = "kubectl get ns"
        print("\033[1;32;40m%s\033[0m" % cmd)
        os.system(cmd)
        print("\033[1;32;40m%s\033[0m" % "\nK8S clusters 管理使用说明")
        print("\033[1;32;40m%s\033[0m" % "1. ks","选择需要连接的kubernetes(如果存在多个~/.kube/kubeconfig*,可以把 kubeconfig 存放命令为 kubeconfig-hz,kubeconfig-sh)")
        print("\033[1;32;40m%s\033[0m" % "2. ki","列出所有 Namespace")
        print("\033[1;32;40m%s\033[0m" % "3. ki xx","列出某 Namespace (如果存在多个 ~/.kube/kubeconfig*,将在其中找到最优匹配) 的 Pod,Namespace 参数支持模糊匹配,例如要查看 Namespace 为 dev 里的 pod,可以简写为 'ki d',输出 pod 列表后 grep: xxx 过滤查询\n         grep: xxx l (可选参数 [ l ] 表示输出目标 Pod 的实时日志)\n         grep: xxx l 100 (表示输出目标 Pod 最新100行的实时日志)\n         grep: xxx l xxx (表示输出目标 Pod 实时日志并过滤指定字符串)\n         grep: xxx r (可选参数 [ r ] 表示重启目标 Pod)\n         grep: xxx o (可选参数 [ o ] 表示导出目标[Deployment,StatefulSet,Service,Ingress,Configmap,Secret] yml文件)\n         grep: xxx del (可选参数 [ del ] 表示删除目标 Pod,根据 k8s 的默认编排策略会重新拉起,类似重启 Pod)\n         grep: xxx cle (可选参数 [ cle ] 表示删除目标 Deployment/StatefulSet)\n         grep: xxx e[si] (可选参数 [ e[si] ] 表示编辑目标 Deploy/Service/Ingress)")
        print("\033[1;32;40m%s\033[0m" % "4. ki xx d","列出某 Namespace 的 Deployment")
        print("\033[1;32;40m%s\033[0m" % "5. ki xx f","列出某 Namespace 的 StatefulSet")
        print("\033[1;32;40m%s\033[0m" % "6. ki xx s","列出某 Namespace 的 Service")
        print("\033[1;32;40m%s\033[0m" % "7. ki xx i","列出某 Namespace 的 Ingress")
    elif sys.argv[1] == '-n' and 2 < len(sys.argv) < 5:
        l = find_ns()
        ns = l[0]
        kubeconfig = l[1]
        result_num = l[-1]
        if ns:
            pod = ""
            obj = "pod"
            ext = " -o wide"
            if len(sys.argv) == 4:
                d = {'d':['deploy'," -o wide"],'s':['service'," -o wide"],'i':['ingress'," -o wide"],'c':['configmap'," -o wide"],'t':['secret'," -o wide"],'n':['node'," -o wide"],'p':['pvc'," -o wide"],'v':['pv'," -o wide"],'f':['sts'," -o wide"],'e':['event','']}
                obj = d[str(sys.argv[3])[0]][0]
                ext = d[str(sys.argv[3])[0]][1]
            while True:
                if pod:
                    pod = str(pod)
                else:
                    cmd = "kubectl --sort-by=.metadata.creationTimestamp get "+obj+ext+" --no-headers -n "+ ns
                    print("\033[1;32;40m%s\033[0m" % cmd)
                    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                    result_lines = p.stdout.readlines()
                    if not result_lines:
                        break
                result_lines = list(filter(lambda x: x.find(pod) >= 0, result_lines))
                if result_lines:
                    for n,e in enumerate(result_lines):
                        print("\033[1;32;40m%s\033[0m"%n,e.strip())
                    if result_num > 1 and n > 7:
                        print("\033[1;32;40m%s\033[0m"%("[ "+kubeconfig+" / "+ns+" ]"))
                    try:
                        pod = input("\033[1;32;35m%s\033[0m\033[5;32;35m%s\033[0m" % ("grep",":"))
                        pod = pod.strip()
                    except:
                        sys.exit()
                    podList = pod.split()
                    pod = podList[0] if podList else ""
                    args = ''.join(podList[1:]) if len(podList) > 1 else "p"
                    if pod.isdigit() and int(pod) < len(result_lines) or len(result_lines) == 1:
                        index = int(pod) if pod.isdigit() else 0
                        res = result_lines[index].split()[0]
                        iip = result_lines[index].split()[5] if len(result_lines[index].split()) > 5 else ''
                        cmd = cmd_obj(ns,obj,res,args,iip)
                        print("\033[1;32;40m%s\033[0m" % cmd)
                        os.system(cmd)
                else:
                    pod = ""
        else:
            print("No namespace found in the kubenetes.")
def main():
    ki()
#-----------------PROG----------------------------
if __name__ == '__main__':
    main()