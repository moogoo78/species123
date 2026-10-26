"""TaiCOL native / alien status against WCVP's Taiwan (TAI) distribution record."""

# TaiCOL alien_type -> the WCVP notion it corresponds to
TAICOL_GROUP = {'native': 'native', 'naturalized': 'introduced', 'invasive': 'introduced', 'casual': 'introduced',
                'cultured': 'cultivated', 'cultivated': 'cultivated'}
# WCVP TAI statuses that still say the plant is native to Taiwan
WCVP_NATIVE = {'native', 'extinct', 'doubtful'}
CHECKS = ('differs', 'wcvp_absent')  # report tabs; 'agree' is not listed


def taiwan_check(alien_type, wcvp_tai):
    """'agree', 'differs', 'wcvp_absent' or None (nothing to compare). wcvp_tai is the TAI status, None when absent.
    A cultivated plant without a WCVP Taiwan record agrees: WCVP does not record cultivation."""
    group = TAICOL_GROUP.get(alien_type)
    if group is None:
        return None
    wcvp = 'native' if wcvp_tai in WCVP_NATIVE else wcvp_tai  # 'introduced' or None
    if group == 'cultivated':
        return 'differs' if wcvp == 'native' else 'agree'
    if wcvp is None:
        return 'wcvp_absent'
    return 'agree' if wcvp == group else 'differs'
