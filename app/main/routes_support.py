from .model import SupportObject, SupportMedia
from flask import render_template

from . import main

picobrew_attribution = "Picobrew, associated product names (Picobrew C/S/Pro, ZSeries, Zymatic, PicoFerm, PicoStill, KegSmarts), equipment icons and Picobrew provided support materials are all trademarks or publicly available intellectual property of Picobrew and is not associated with the production of this software."
community_owner = "Community"


def render_support_template(support_object):
    return render_template('support.html', support_object=support_object, support_object_js=support_object.toJSON())


@main.route('/support/accessories')
def support_accessories():
    acc_support = SupportObject()
    acc_support.name = 'Mini Kegerator'
    acc_support.manual = SupportMedia('/static/support/accessories/MiniKegerator_Manual.pdf')
    return render_support_template(acc_support)


@main.route('/support/pico_c')
def support_pico_c():
    pico_c_support = SupportObject()
    pico_c_support.name = 'Pico C'
    pico_c_support.logo = '/static/img/picobrew.svg'
    pico_c_support.trademark_attribution = picobrew_attribution
    pico_c_support.manual = SupportMedia('/static/support/pico-c/PicoC_Manual.pdf')
    pico_c_support.faq = SupportMedia('/static/support/pico-c/Frequently-Asked-Questions.md')
    pico_c_support.instructional_videos = SupportMedia('/static/support/pico-c/Instructional-Videos.md')
    pico_c_support.misc_media = {
        'DIY Cleaning Bucket': SupportMedia('/static/support/pico-c/DIY_CleaningBucket.pdf'),
        'Cold Brew': SupportMedia('/static/support/pico-c/PicoC_ColdBrew.pdf'),
        'Manual Brew': SupportMedia('/static/support/pico-c/PicoC_ManualBrew.pdf'),
        'Sous Vide': SupportMedia('/static/support/pico-c/PicoC_SousVide.pdf'),
        'Troubleshooting': SupportMedia('/static/support/pico-c/PicoC_Troubleshooting.pdf'),
    }
    return render_support_template(pico_c_support)


@main.route('/support/pico_pro')
def support_pico_pro():
    pico_pro_support = SupportObject()
    pico_pro_support.name = 'Pico Pro'
    pico_pro_support.logo = '/static/img/picobrew.svg'
    pico_pro_support.trademark_attribution = picobrew_attribution
    pico_pro_support.manual = SupportMedia('/static/support/pico-pro/PicoPro_Manual.pdf')
    pico_pro_support.faq = SupportMedia('/static/support/pico-pro/Frequently-Asked-Questions.md')
    pico_pro_support.instructional_videos = SupportMedia('/static/support/pico-pro/Instructional-Videos.md')
    pico_pro_support.misc_media = {
        'Cold Brew': SupportMedia('/static/support/pico-pro/PicoPro_ColdBrew.pdf'),
        'Manual Brew': SupportMedia('/static/support/pico-pro/PicoPro_ManualBrew.pdf'),
        'Sous Vide': SupportMedia('/static/support/pico-pro/Pico_SousVide.pdf'),
        'Troubleshooting': SupportMedia('/static/support/pico-pro/Pico_Troubleshooting.pdf'),
    }
    return render_support_template(pico_pro_support)


@main.route('/support/picoferm')
def support_picoferm():
    picoferm_support = SupportObject()
    picoferm_support.name = 'PicoFerm'
    picoferm_support.logo = '/static/img/picoferm.svg'
    picoferm_support.trademark_attribution = picobrew_attribution
    picoferm_support.manual = SupportMedia('/static/support/picoferm/PicoFerm_Manual.pdf')
    picoferm_support.misc_media = {
        'Wifi Setup': SupportMedia('/static/support/picoferm/Wifi-setup.png', community_owner),
        'Troubleshooting': SupportMedia('/static/support/picoferm/PicoFerm_Troubleshooting.pdf'),
    }
    return render_support_template(picoferm_support)


@main.route('/support/iSpindel')
def support_iSpindel():
    iSpindel_support = SupportObject()
    iSpindel_support.name = 'iSpindel'
    iSpindel_support.logo = '/static/img/iSpindel.svg'
    iSpindel_support.faq = SupportMedia('/static/support/iSpindel/iSpindel.md', community_owner)
    iSpindel_support.instructional_videos = SupportMedia('/static/support/iSpindel/Instructional-Videos.md', community_owner)
    iSpindel_support.misc_media = {}
    return render_support_template(iSpindel_support)


@main.route('/support/tilt')
def support_tilt():
    tilt_support = SupportObject()
    tilt_support.name = 'Tilt'
    tilt_support.logo = '/static/img/tilt.svg'
    tilt_support.trademark_attribution = "Tilt and the associated bottlecap logo are trademarks of Baron Brew Equipment and is not associated with the production of this software."
    tilt_support.faq = SupportMedia('/static/support/tilt/tilt.md', community_owner)
    tilt_support.instructional_videos = SupportMedia('/static/support/tilt/Instructional-Videos.md', "Baron Brew Equipment")
    tilt_support.misc_media = {}
    return render_support_template(tilt_support)


@main.route('/support/picostill')
def support_picostill():
    picostill_support = SupportObject()
    picostill_support.name = 'PicoStill'
    picostill_support.logo = '/static/img/picostill.svg'
    picostill_support.trademark_attribution = picobrew_attribution
    picostill_support.manual = SupportMedia('/static/support/picostill/PicoStill_Manual.pdf')
    picostill_support.instructional_videos = SupportMedia('/static/support/picostill/Instructional-Videos.md')
    picostill_support.misc_media = {
        'Troubleshooting': SupportMedia('/static/support/picostill/PicoStill_Troubleshooting.pdf'),
        'Wifi Setup': SupportMedia('/static/support/picostill/picostill-wifi-setup.png', community_owner),
        'Light Reference': SupportMedia('/static/support/picostill/PicoStill_Lights.jpg', community_owner),
        'Setup Instructions': SupportMedia('/static/support/picostill/picostill-setup-instructions.png', community_owner),
        'Program Functions': SupportMedia('/static/support/picostill/picostill-program-functions.png', community_owner),
        'Utility Functions': SupportMedia('/static/support/picostill/picostill-utility-functions.png', community_owner),
        'Firmware Network Info': SupportMedia('/static/support/picostill/picostill-wifi-setup.png', community_owner),
    }
    return render_support_template(picostill_support)


@main.route('/support/z_series')
def support_z_series():
    z_series_support = SupportObject()
    z_series_support.name = 'Z Series'
    z_series_support.logo = '/static/img/zseries.svg'
    z_series_support.trademark_attribution = picobrew_attribution
    z_series_support.manual = SupportMedia('/static/support/z-series/ZN_AssemblyGuide.pdf')
    z_series_support.faq = SupportMedia('/static/support/z-series/Frequently-Asked-Questions.md')
    z_series_support.misc_media = {
        'Quick Start': SupportMedia('/static/support/z-series/Z_QuickStart.pdf'),
        'Bottling Kit': SupportMedia('/static/support/z-series/Z_BottlingKit.pdf'),
        'Draft Kit': SupportMedia('/static/support/z-series/Z_DraftKit.pdf'),
        'Troubleshooting': SupportMedia('/static/support/z-series/Z_Troubleshooting.pdf'),
    }
    return render_support_template(z_series_support)


@main.route('/support/additional_info')
def support_additional():
    additional_support = SupportObject()
    additional_support.name = 'Additional Resources'
    additional_support.misc_media = {
        'picobrew_pico': SupportMedia('https://github.com/chiefwigms/picobrew_pico', community_owner),
        'picobrew-support': SupportMedia('https://github.com/Intecpsp/picobrew-support', community_owner),
        'Awesome-Picobrew': SupportMedia('https://github.com/manofthemountain/awesome-picobrew', community_owner),
        'Facebook Group - Picobrewers': SupportMedia('https://www.facebook.com/groups/Picobrewers', community_owner),
        'Reddit - Picobrew': SupportMedia('https://www.reddit.com/r/picobrew/', community_owner),
        'HomebrewTalk - PicoBrew Zymatic': SupportMedia('https://www.homebrewtalk.com/threads/picobrew-zymatic.434787/', community_owner),
        'HomebrewTalk - PicoBrew Z': SupportMedia('https://www.homebrewtalk.com/threads/picobrew-z.645332/', community_owner),
        'HomebrewTalk - Picobrew Pico Users': SupportMedia('https://www.homebrewtalk.com/threads/picobrew-pico-users.593969/', community_owner),
        'Community Forum - Picobrewers': SupportMedia('https://picobrewers.org', community_owner),
        'PicoFree - Bring Your Own Ingredients Kit': SupportMedia('https://www.pico-free.com', community_owner),
    }
    return render_support_template(additional_support)


@main.route('/support/kegsmarts')
def support_kegsmarts():
    kegsmarts_support = SupportObject()
    kegsmarts_support.name = 'KegSmarts'
    kegsmarts_support.trademark_attribution = picobrew_attribution
    kegsmarts_support.manual = SupportMedia('/static/support/legacy/kegsmarts/KegSmarts_Manual.pdf')
    kegsmarts_support.misc_media = {
        'Firmware': SupportMedia('/static/support/legacy/kegsmarts/Firmware.md'),
        'Firmware-Installation': SupportMedia('/static/support/legacy/kegsmarts/Firmware-Installation.md'),
        'Troubleshooting': SupportMedia('/static/support/legacy/kegsmarts/KegSmarts_Troubleshooting.pdf'),
    }
    return render_support_template(kegsmarts_support)


@main.route('/support/pico_s')
def support_pico_s():
    pico_s_support = SupportObject()
    pico_s_support.name = 'Pico S'
    pico_s_support.logo = '/static/img/picobrew.svg'
    pico_s_support.trademark_attribution = picobrew_attribution
    pico_s_support.manual = SupportMedia('/static/support/legacy/pico-s/Pico_Manual.pdf')
    pico_s_support.faq = SupportMedia('/static/support/legacy/pico-s/Frequently-Asked-Questions.md')
    pico_s_support.instructional_videos = SupportMedia('/static/support/legacy/pico-s/Instructional-Videos.md')
    pico_s_support.misc_media = {
        'Troubleshooting': SupportMedia('/static/support/legacy/legacy/pico-s/Pico_Troubleshooting.pdf'),
    }
    return render_support_template(pico_s_support)


@main.route('/support/zymatic')
def support_zymatic():
    zymatic_support = SupportObject()
    zymatic_support.name = 'Zymatic'
    zymatic_support.logo = '/static/img/zymatic.svg'
    zymatic_support.trademark_attribution = picobrew_attribution
    zymatic_support.manual = SupportMedia('/static/support/legacy/zymatic/Zymatic_Manual.pdf')
    zymatic_support.faq = SupportMedia('/static/support/legacy/zymatic/Frequently-Asked-Questions.md')
    zymatic_support.instructional_videos = SupportMedia('/static/support/legacy/zymatic/Instructional-Videos.md')
    zymatic_support.misc_media = {
        'Firmware': SupportMedia('/static/support/legacy/zymatic/Firmware.md'),
        'Firmware-Installation': SupportMedia('/static/support/legacy/zymatic/Firmware-Installation.md'),
        'Maintenance': SupportMedia('/static/support/legacy/zymatic/Maintenance.md'),
        'Troubleshooting': SupportMedia('/static/support/legacy/zymatic/Zymatic_Troubleshooting.pdf'),
    }
    return render_support_template(zymatic_support)
