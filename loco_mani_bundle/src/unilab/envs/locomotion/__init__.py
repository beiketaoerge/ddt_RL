"""Locomotion env registry bootstrap contract."""

# Bundle trim: only go2_arm is shipped in this loco-mani bundle.
# Upstream also registers go1 / go2 / go2w / g1 here.
__unilab_registry_modules__ = ("unilab.envs.locomotion.go2_arm", "unilab.envs.locomotion.d1_arm",)
