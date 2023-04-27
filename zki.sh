function parse_git_branch() {
  [ -e ./.git/HEAD ] && echo -e "* \033[32m$(awk -F/ '{print $NF}' ./.git/HEAD)\033[0m"
}
source <(kubectl completion bash)
export EDITOR=vim
export KUBE_EDITOR=vim
export KI_LINE=$([ -e ~/.history/.line ] && cat ~/.history/.line || echo 200)
export PS1="\e[1;37m[\e[m\e[1;32m\u\e[m\e[1;32m@\e[m\e[1;35m\H\e[m \e[1;33m\A\e[m \w\e[m\e[1;37m]\e[m\e[1;36m\e[m \$(/usr/local/bin/ki --w) \$(parse_git_branch) \n\\$ "
alias vi=vim
alias ls='ls --color'
alias ll='ls -l'
[ $USER = root ] && STYLE="\033c\033[5;32m%s\033[1;m\n" || STYLE="\033[5;32m%s\033[1;m\n"
[[ $- == *i* ]] && [ -e ~/.kube/config ] && printf $STYLE "$(/usr/local/bin/ki --w)"
