from .model import SupportObject
from flask import render_template

from . import main


@main.route('/support/accessories')
def support_accessories():
    acc_support = SupportObject()
    acc_support.name = 'Mini Kegerator'
    acc_support.manual_path = '/static/support/accessories/MiniKegerator_Manual.pdf'
    return render_template('support.html', support_object=acc_support)


@main.route('/support/pico_c')
def support_pico_c():
    pico_c_support = SupportObject()
    pico_c_support.name = 'Pico C'
    pico_c_support.manual_path = '/static/support/pico-c/PicoC_Manual.pdf'
    pico_c_support.faq_path = '/static/support/pico-c/Frequently-Asked-Questions.md'
    pico_c_support.instructional_videos_path = '/static/support/pico-c/Instructional-Videos.md'
    pico_c_support.misc_media = {
        'DIY Cleaning Bucket' : '/static/support/pico-c/DIY_CleaningBucket.pdf',
        'Cold Brew' : '/static/support/pico-c/PicoC_ColdBrew.pdf',
        'Manual Brew' : '/static/support/pico-c/PicoC_ManualBrew.pdf',
        'Sous Vide' : '/static/support/pico-c/PicoC_SousVide.pdf'
    }
    return render_template('support.html', support_object=pico_c_support)


@main.route('/support/pico_pro')
def support_pico_pro():
    pico_pro_support = SupportObject()
    pico_pro_support.name = 'Pico Pro'
    pico_pro_support.manual_path = '/static/support/pico-pro/PicoPro_Manual.pdf'
    pico_pro_support.faq_path = '/static/support/pico-pro/Frequently-Asked-Questions.md'
    pico_pro_support.instructional_videos_path = '/static/support/pico-pro/Instructional-Videos.md'
    pico_pro_support.misc_media = {
        'Cold Brew' : '/static/support/pico-pro/PicoPro_ColdBrew.pdf',
        'Manual Brew' : '/static/support/pico-pro/PicoPro_ManualBrew.pdf',
        'Sous Vide' : '/static/support/pico-pro/Pico_SousVide.pdf'
    }
    return render_template('support.html', support_object=pico_pro_support)


@main.route('/support/picoferm')
def support_picoferm():
    picoferm_support = SupportObject()
    picoferm_support.name = 'PicoFerm'
    picoferm_support.manual_path = '/static/support/picoferm/PicoFerm_Manual.pdf'
    picoferm_support.misc_media = {
        'Wifi Setup' : '/static/support/picoferm/Wifi-setup.png'
    }
    return render_template('support.html', support_object=picoferm_support)


@main.route('/support/picostill')
def support_picostill():
    picostill_support = SupportObject()
    picostill_support.name = 'PicoStill'
    picostill_support.manual_path = '/static/support/picostill/PicoStill_Manual.pdf'
    picostill_support.instructional_videos_path = '/static/support/picostill/Instructional-Videos.md'
    picostill_support.misc_media = {
        'Light Reference' : '/static/support/picostill/PicoStill_Lights.jpg'
    }
    return render_template('support.html', support_object=picostill_support)


@main.route('/support/z_series')
def support_z_series():
    z_series_support = SupportObject()
    z_series_support.name = 'Z Series'
    z_series_support.manual_path = '/static/support/z-series/ZN_AssemblyGuide.pdf'
    z_series_support.faq_path = '/static/support/z-series/Frequently-Asked-Questions.md'
    z_series_support.misc_media = {
        'Quick Start' : '/static/support/z-series/Z_QuickStart.pdf',
        'Bottling Kit' : '/static/support/z-series/Z_BottlingKit.pdf',
        'Draft Kit' : '/static/support/z-series/Z_DraftKit.pdf'
    }
    return render_template('support.html', support_object=z_series_support)


@main.route('/support/additional_info')
def support_additional():
    additional_support = SupportObject()
    additional_support.name = 'Additional Resources'
    additional_support.misc_media = {
        'picobrew_pico' : 'https://github.com/chiefwigms/picobrew_pico',
        'picobrew-support' : 'https://github.com/Intecpsp/picobrew-support',
        'Awesome-Picobrew' : 'https://github.com/manofthemountain/awesome-picobrew'
    }
    return render_template('support.html', support_object=additional_support)


@main.route('/support/kegsmarts')
def support_kegsmarts():
    kegsmarts_support = SupportObject()
    kegsmarts_support.name = 'KegSmarts'
    kegsmarts_support.manual_path = '/static/support/legacy/kegsmarts/KegSmarts_Manual.pdf'
    kegsmarts_support.misc_media = {
        'Firmware' : '/static/support/legacy/kegsmarts/Firmware.md',
        'Firmware-Installation' : '/static/support/legacy/kegsmarts/Firmware-Installation.md'
    }
    return render_template('support.html', support_object=kegsmarts_support)


@main.route('/support/pico_s')
def support_pico_s():
    pico_s_support = SupportObject()
    pico_s_support.name = 'Pico S'
    pico_s_support.manual_path = '/static/support/legacy/pico-s/Pico_Manual.pdf'
    pico_s_support.faq_path = '/static/support/legacy/pico-s/Frequently-Asked-Questions.md'
    pico_s_support.instructional_videos_path = '/static/support/legacy/pico-s/Instructional-Videos.md'
    return render_template('support.html', support_object=pico_s_support)


@main.route('/support/zymatic')
def support_zymatic():
    zymatic_support = SupportObject()
    zymatic_support.name = 'Zymatic'
    zymatic_support.manual_path = '/static/support/legacy/zymatic/Zymatic_Manual.pdf'
    zymatic_support.faq_path = '/static/support/legacy/zymatic/Frequently-Asked-Questions.md'
    zymatic_support.instructional_videos_path = '/static/support/legacy/zymatic/Instructional-Videos.md'
    zymatic_support.misc_media = {
        'Firmware' : '/static/support/legacy/zymatic/Firmware.md',
        'Firmware-Installation' : '/static/support/legacy/zymatic/Firmware-Installation.md',
        'Maintenance' : '/static/support/legacy/zymatic/Maintenance.md'
    }
    return render_template('support.html', support_object=zymatic_support)
