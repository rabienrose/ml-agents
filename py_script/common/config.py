import os
import oss2
import pymongo
use_internal=False
if use_internal:
    url="mongodb://root:La_009296@dds-2zedc1c8efae92d4118430.mongodb.rds.aliyuncs.com:3717/admin"
    endpoint = os.getenv('OSS_TEST_ENDPOINT', 'https://oss-cn-beijing-internal.aliyuncs.com') # internal net

else:
    url="mongodb://root:La_009296@dds-2zedc1c8efae92d4-pub.mongodb.rds.aliyuncs.com:3717/admin"
    endpoint = os.getenv('OSS_TEST_ENDPOINT', 'https://oss-cn-beijing.aliyuncs.com') # external net
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', 'LTAI4GJDtEd1QXeUPZrNA4Yc')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', 'rxWAZnXNhiZ8nemuvshvKxceYmUCzP')
bucket_name='monster-war'

def get_config():
    bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
    myclient = pymongo.MongoClient(url)
    return [bucket, myclient]

def drop_db(db_name):
    myclient = pymongo.MongoClient(url)
    myclient.drop_database(db_name)

def list_db():
    myclient = pymongo.MongoClient(url)
    for db in myclient.list_databases():
        print(db)

