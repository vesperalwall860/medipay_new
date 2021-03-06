import os
import random
import re
import string
import io
import csv
import grp
import pwd

from flask import request, session, url_for, make_response
from flask_login import current_user
from werkzeug.utils import secure_filename

from .. import config, redis_store, socketio


def prepare_gop_dict(gop):
    '''The function takes the GOP model object
    and convert it to the python dictionary'''

    if not gop.timestamp_edited:
        timestamp_edited = None
    else:
        timestamp_edited = gop.timestamp_edited.strftime('%I:%M %p %m/%d/%Y')

    icd_codes_ids = []
    for icd_code in gop.icd_codes:
        icd_codes_ids.append(icd_code.id)

    gop_dict = {
        'id': gop.id,
        'provider_id': str(gop.provider.id),
        'payer_id': str(gop.payer.id),
        'member_id': str(gop.member.id),
        'payer_company': gop.payer.company,
        'provider_company': gop.provider.company,
        'member_name': gop.member.name,
        'member_dob': gop.member.dob,
        'member_tel': gop.member.tel,
        'member_gender': gop.member.gender,
        'policy_number': gop.policy_number,
        'icd_codes': icd_codes_ids,
        'patient_action_plan': gop.patient_action_plan,
        'doctor_notes': gop.doctor_notes,
        'admission_date': gop.admission_date.strftime('%m/%d/%Y'),
        'admission_time': gop.admission_time.strftime('%I:%M %p'),
        'reason': gop.reason,
        'doctor_name': gop.doctor_name,
        'room_price': gop.room_price,
        'room_type': gop.room_type,
        'patient_medical_no': gop.patient_medical_no,
        'doctor_fee': gop.doctor_fee,
        'surgery_fee': gop.surgery_fee,
        'medication_fee': gop.medication_fee,
        'quotation': gop.quotation,
        'timestamp': gop.timestamp.strftime('%I:%M %p %m/%d/%Y'),
        'status': gop.status,
        'state': gop.state,
        'reason_decline': gop.reason_decline,
        'reason_close': gop.reason_close,
        'timestamp_edited': timestamp_edited,
        'stamp_author': gop.stamp_author,
        'turnaround_time': gop.turnaround_time()
    }

    return gop_dict


def prepare_gops_list(gops):
    '''The function takes the GOP model objects list and convert it to the
    python dictionary'''

    if not gops:
        return []

    # initialize the results list
    results = []

    for gop in gops:
        results.append(prepare_gop_dict(gop))

    return results


def allowed_file(filename):
    '''
    checks if the uploaded file contains only the required extensions
    '''
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config['production'].ALLOWED_EXTENSIONS


def pass_generator(size=6, chars=string.ascii_uppercase + string.digits):
    '''
    generates a 6 digit random password
    '''
    return ''.join(random.choice(chars) for _ in range(size))


def photo_file_name_santizer(photo):
    '''
    stores the uploaded image file
    '''
    filename = secure_filename(photo.data.filename)

    if filename and allowed_file(filename):
        filename = str(random.randint(100000, 999999)) + filename
        filepath = os.path.join(config['production'].UPLOAD_FOLDER, filename)
        photo.data.save(filepath)

        # Give the uploaded file read rights to everyone
        uid = pwd.getpwnam("medipay2").pw_uid
        gid = grp.getgrnam("nobody").gr_gid
        os.chown(filepath, uid, gid)

    if not filename:
        filename = ''

    if filename:
        photo_filename = '/static/uploads/' + filename
    else:
        photo_filename = '/static/img/person-solid.png'

    return photo_filename


def csv_ouput(csv_file_name, data):
    '''
    genrates the csv file format
    '''
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(data)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=%s.csv" %csv_file_name
    output.headers["Content-type"] = "text/csv"
    return output


def to_float_or_zero(value):
    '''
    converts strings to float if valid float number, else defaults the value to 0.0
    '''
    try:
        value = float(value)
    except ValueError:
        value = 0.0
    return value


def validate_email_address(data):
    '''
    return true if the email address is validated else false
    '''
    if data:
        match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"\
          ,data)
        if match == None:
            return False

        if len(data) < 1 or len(data) > 64:
            return False

        return True


def notify(title='New notification', message='Message',
           url=None, user=current_user, user_id=None,
           room_name=None):
    '''
    function to send socketio message
    '''
    try:
        # if the user's id is not passed,
        # use the User object instead
        if not user_id:
            user_id = user.id

        socketio.emit('message',
                      {'title': title,
                       'message': message,
                       'url': url,
                       'room_name': room_name},
                      room=user_id)
    except:
        pass


def is_admin(user):
    '''
    checks if the user is admin
    '''
    return user.get_role() == 'admin'


def is_provider(user):
    '''
    checks if the user is a provider
    '''
    return user.get_type() == 'provider'


def is_payer(user):
    '''
    checks if the user is a payer
    '''
    return user.get_type() == 'payer'


def to_str(bytes_or_str):
    '''
    converts the data to string
    '''
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value # Instance of str


def to_bytes(bytes_or_str):
    '''
    converts the data to bytes
    '''
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode('utf-8')
    else:
        value = bytes_or_str
    return value # Instance of bytes
