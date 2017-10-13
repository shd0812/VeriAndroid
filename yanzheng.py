#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "youxian_Tester <sx.work@outlook.com> 2016-04-13"
__vserion__ = "v1.0"

''' 
环境依赖Java,python2.7(需要安装requests/pandas库) 安装命令( pip install pandas)
通过反编译android apk，获取AndroidManifest.xml文件中的渠道号等各项key信息
'''

import os,sys
import shutil
import re
import requests
import csv
import time
import random
from pandas import DataFrame,Series
import pandas as pd
import readconfig
import appiumlog


rc = readconfig.ReadConfig()
log = appiumlog.Clog()
log.build_start_line()

#设置安卓渠道版本所在目录
version_catalogue = rc.getOther('chanel_path')
#version_catalogue = str(raw_input(" \n -> Please input App Channel catalogue: "))
#设置ApkTool的目录
ApkTool = rc.getOther('apkTool_path')
now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

#apktool.jar地址
apktool_download_url = 'https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.1.0.jar'

#存放测试结果
script_dir = os.getcwd()

try:
	if os.path.isdir(version_catalogue):
		
		#abc = []
		#for cv in os.listdir(version_catalogue):
			#if os.path.splitext(cv)[1] == '.apk':
				#abc.append(cv)
		
		
		vapk = [ cv for cv in os.listdir(version_catalogue) if os.path.splitext(cv)[1] == '.apk' ]
		
		if len(vapk) !=0:
			
			print(" -> Total: \033[1;37;42m {0} \33[0m Apk. ".format(len(vapk)))
		else:
			print(" -> No has ApkFile.")
			raise NameError
except (NameError,OSError,IOError):
	print(" -> Error: Please check File PATH.")
	sys.exit()
else:
	os.chdir(version_catalogue)

#拷贝或下载apktool.jar反编译工具
if os.path.exists(os.path.join(version_catalogue,'apktool.jar')):
	print(" ->{0} Has found a decompiler apktool.jar.\n".format(version_catalogue))
elif os.path.isfile(ApkTool):
	shutil.copy(ApkTool,version_catalogue)
else:
	with open('apktool.jar','wb') as atool:
		log.build_case(" -> The Computer is not exists apktools.jar,Will begining Download Apktools.jar......")
		print(" -> The Computer is not exists apktools.jar,Will begining Download Apktools.jar......")
		atool.write(requests.get(apktool_download_url).content)

start_time = time.time()

#反编译android apk
def decompiler(vdir):
	vapk = [ cv for cv in os.listdir(vdir) if os.path.splitext(cv)[1] == '.apk' ]
	#log.build_case(" -> 一共发现了{0} 个apk,is in decomopiling,Please wait.....\n".format(len(vapk)))
	print(" -> The Path has found {0} channel version,is in decomopiling,Please wait.....\n".format(len(vapk))) 
	for idx,apk in enumerate(vapk):
		channeldir,extension = os.path.splitext(apk)
		if os.path.isdir(channeldir):
			pass
		else:
			print(" -> The \033[1;37;44m {0} \33[0m Apk is processing 11: {1}".format(idx,apk))
			
			os.popen('java -jar apktool.jar d -s {0}'.format(apk))
	reverse_apk_folder = [ opf for opf in os.listdir(vdir) if os.path.isdir(opf) ]
	print("-------------------------------------------------------------------")
	print(" -> {0} Finish Apk decompiling.".format(now))
	print(" -> Total: \033[1;32;44m {0} \33[0m Apk Floder. ".format(len(reverse_apk_folder)))
	return vapk,reverse_apk_folder

#处理AndroidManifest.xml文件
def handling(filename,text):
	textual_value = ""
	with open(filename,'r+') as m:
		line = [ line.strip() for line in m.readlines() if text in line ]
		for n in line:
			value = n.split('=')[2]
			#使用strip过滤"/>//--等特殊字符
			textual_value = value.strip('"/>// --')
	return textual_value

#遍历反编译后的apk文件夹，通过AndroidManifest.xml文件获取渠道号
def get_apk_umeng_value(reverse_folder):
	#设置要查找的文本
	text_umeng_channel = "UMENG_CHANNEL"
	text_umeng_appkey = "UMENG_APPKEY"
	text_umeng_message_secret = "UMENG_MESSAGE_SECRET"
	text_easemob_appkey = "EASEMOB_APPKEY"
	text_amap = "com.amap.api.v2.apikey"

	umeng_channel = []
	umeng_appkey = []
	umeng_message_secret = []
	easemob_appkey = []
	amap = []

	for rfn in reverse_folder:
		manifest = os.path.join(version_catalogue,rfn,'AndroidManifest.xml')
		#友盟渠道号
		umeng_channel.append(handling(manifest,text_umeng_channel))
		#友盟appkey
		umeng_appkey.append(handling(manifest,text_umeng_appkey))
		#友盟UMENG_MESSAGE_SECRET
		umeng_message_secret.append(handling(manifest,text_umeng_message_secret))
		#环信
		easemob_appkey.append(handling(manifest,text_easemob_appkey))
		#高德地图
		amap.append(handling(manifest,text_amap))
	return umeng_channel,umeng_appkey,umeng_message_secret,easemob_appkey,amap

#随机取签名
def get_apk_signature(reverse_folder):
	try:
		cert_path = "original//META-INF"
		cert = [ os.path.join(version_catalogue,folder,cert_path,'JIUAI.RSA') for folder in reverse_folder ]
		num = random.randint(0,len(cert))
		return os.popen('keytool.exe -printcert -v -file {0}'.format(cert[num])).read()
	except:
		pass

#验证app签名
apkname,reverse_folder = decompiler(version_catalogue)
with open(script_dir + "//signature.txt",'wb') as s:
	signature_info = get_apk_signature(reverse_folder)
	s.writelines(signature_info)


#输出测试结果：比较渠道包中的apk与开发提供的渠道号是否一致，不一致输出2，一致输入1
def output_test_results():

	#获取apk名称和友盟渠道号
	apkname,reverse_folder = decompiler(version_catalogue)
	umeng_channel_value,umeng_appkey_value,umeng_message_secret_value,easemob_appkey_value,amap_value = get_apk_umeng_value(reverse_folder)
	print len(umeng_channel_value)
	msg = '一共有'+ str(len(umeng_channel_value))+"个包"
	#print msg
	log.build_case(msg)
	log.build_case(umeng_channel_value)
	offical_channel=[];
	#取出开发提供的渠道号
	print rc.getOther('officalChanel_path')
	with open(rc.getOther('officalChanel_path'),'r') as pf:
		lines=pf.readlines()
		#print lines
		i = 0
		for line in lines:
			i+=1
			
				
			if line[-7:-1] in umeng_channel_value:
				log.build_case('第%d 个测试通过' % i)
				#print line[-7:-1]
				print u'第%d 个测试通过' % i
			else:
				msg = line[-7:-1]+'测试失败'
				log.build_case(msg)
				#print line[-7:-1]
				print line[-7:-1]
	log.build_end_line()			
		
	#list1 = []
	#print umeng_channel_value
	#for  i in range(len(umeng_channel_value)):
		#print i
		#c =[]
		#c.append(umeng_channel_value[i])
		#c.append(apkname[i])
		
		#list1.append(c)
	#list1 = [[1,2],[1,2],[1,2]]
	#print list1
	#with open('d:\chanels.txt','wb') as pf:
		#for list2 in list1:
			#print list2
			#list2 = repr(list2)+'\n'
			#pf.write(list2)
	
	


output_test_results()


