# polybar systemd
I'm still testing this stuff so don't get upset if it doesn't work.

## Method 1 - Hybrid of user and system
User level systemd doesn't understand `suspend.target` or `hibernate.target` and this is why we'll use a hybrid approach here.

### polybar.service
1. Copy `hybrid/polybar.service` to `~/.config/systemd/user` and modify it to your liking
2. Execute `systemctl --user daemon-reload`
3. Execute `systemctl --user enable --now polybar`

### polybar-resume.service
1. Copy `hybrid/polybar-resume.service` to `/etc/systemd/system` and modify it to your liking
2. Execute `sudo systemctl daemon-reload`
3. Execute `sudo systemctl enable polybar-resume.service`

## Method 2 - Pure user-level

## polybar-resume.sh
1. Copy `user/polybar-resume.sh` to `~/.config/polybar` and modify it to your liking

### polybar.service
1. Copy `user/polybar.service` to `~/.config/systemd/user` and modify it to your liking
2. Execute `systemctl --user daemon-reload`
3. Execute `systemctl --user enable --now polybar`

### polybar-resume.service
1. Copy `user/polybar-resume.service` to `~/.config/systemd/user` and modify it to your liking
2. Execute `systemctl --user daemon-reload`
3. Execute `systemctl --user enable --now polybar-resume.service`
