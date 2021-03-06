# -*- coding: utf-8 -*-
import pretty_errors
import os
from LogHelper import LogHelper
from UperInfo import UperInfo 
from PreProcess import PreProcess 
from Downloader import Downloader
from Common import RandomSleep
from middlewares import middleware

from BiliSpider import BiliSpider
# from Test2 import GithubDeveloperSpider

def MainProcess(uperList, saveRootPath, concurrency = 3):
    logger = LogHelper('Bili', cmdLevel='INFO', fileLevel="DEBUG").logger
    pp = None
    try:
        # --------------------------------------------------------------
        # 进行每个 UP 主视频页数的获取
        pp = PreProcess(logger = logger, uperList=uperList)
        pp.ScanLoclInfo(saveRootPath)
        pp.Process()
        # --------------------------------------------------------------
        # 爬取要下载视频的 url
        for uper in pp.uperList:
            logger.info(uper.UserName + " Spider Start···")
            OneSpiderRetryTimes = 0
            # 打算下载的数量，要去网络动态获取的数量进行对比
            while ((uper.NeedDownloadFilmCount > len(uper.VideoInfoDic_NetFileName) or len(uper.ErrorUrl_Dic) > 0) and OneSpiderRetryTimes <= 10):
                # dd = BiliSpider()
                # GithubDeveloperSpider
                BiliSpider.start(logger = logger,
                                uper = uper,
                                saveRootPath = saveRootPath,
                                concurrency = concurrency,
                                middleware=middleware)
                                
                OneSpiderRetryTimes = OneSpiderRetryTimes + 1
                logger.info("Try Spider " + uper.UserName + " " + str(OneSpiderRetryTimes) + " times.")
                RandomSleep()
                
            logger.info(uper.UserName + " Spider Done.")

            if OneSpiderRetryTimes > 10:
                logger.error(uper.UserName + " Spider Retry " + str(OneSpiderRetryTimes) + "times.")
                logger.error("Error Url:")
                for eUrl in uper.ErrorUrl_Dic:
                    logger.error(eUrl)
            else:
                # 本地应该原有+准备要下载的 != 网络总数，需要提示
                if len(uper.VideoInfoDic_NetFileName) != len(uper.VideoInfoDic_loaclFileName):
                    logger.warn("VideoInfoDic_NetFileName Count: " + str(len(uper.VideoInfoDic_NetFileName)) 
                        + " != VideoInfoDic_loaclFileName Count: " + str(len(uper.VideoInfoDic_loaclFileName))
                    )
            uper.ErrorUrl_Dic.clear()

        logger.info("Spider All Done.")
        # --------------------------------------------------------------
        logger.info("Start Download"+ "----" * 20)
        # 开始下载
        # 先对 local 与 net 的字典进行同步
        logger.info("Start Sync Dic")
        for uper in pp.uperList:
            iNeedDl = 0
            for fileName, oneVideo in zip(uper.VideoInfoDic_loaclFileName.keys(), uper.VideoInfoDic_loaclFileName.values()):
                if fileName in uper.VideoInfoDic_NetFileName:
                    uper.VideoInfoDic_NetFileName[fileName].isDownloaded = oneVideo.isDownloaded
                    if oneVideo.isDownloaded == False:
                        iNeedDl = iNeedDl + 1
            logger.info(uper.UserName + "NetFile / LocalFile -- NeedDl: " + str(len(uper.VideoInfoDic_NetFileName)) + " / " + str(len(uper.VideoInfoDic_loaclFileName)) + " -- " + str(iNeedDl))
        logger.info("End Sync Dic")
        for uper in pp.uperList:
            directory = os.path.join(saveRootPath, uper.UserName)
            for fileName, oneVideo in zip(uper.VideoInfoDic_NetFileName.keys(), uper.VideoInfoDic_NetFileName.values()):
                if oneVideo.isDownloaded == True:
                    continue
                DownloadRetryTimes = 0
                oneRe = False
                while oneRe is False and DownloadRetryTimes <= 10:
                    oneRe = Downloader(logger, directory, oneVideo.time, oneVideo.title, oneVideo.url).ProcessOne()
                    DownloadRetryTimes = DownloadRetryTimes + 1
                    logger.info("Try Download " + str(DownloadRetryTimes) + " times.")
                    RandomSleep()

                if OneSpiderRetryTimes > 10:
                    logger.error("Retry Download " + str(DownloadRetryTimes) + " times.")
                    logger.error("Error Url: " + oneVideo.url)
                # 标记下载完成
                if oneRe:
                    oneVideo.isDownloaded = True
                    uper.ThisTimeDownloadCount = uper.ThisTimeDownloadCount + 1
                    

    except Exception as ex:
        errInfo = "Catch Exception: " + str(ex)
        logger.error(errInfo)
    finally:
        logger.info("finally"+ "----" * 20)
        for uper in pp.uperList:
            logger.info("This Time Download: " + uper.UserName + " -- " + str(uper.ThisTimeDownloadCount))
        for uper in pp.uperList:
            for fileName, oneVideo in zip(uper.VideoInfoDic_NetFileName.keys(), uper.VideoInfoDic_NetFileName.values()):
                if oneVideo.isDownloaded == False:
                    logger.error('Download Fail:' + uper.UserName)
                    logger.error(oneVideo.url)
        logger.info("All Done.")

if __name__ == '__main__':
    # --------------------------------------------------------------
    # 设置需要下载的信息
    # 每个 UP 主视频的总数
    uperList = []
    # https://space.bilibili.com/9458053/video
    #                        用户名        用户的 VideoPage ID数
    uperList.append(UperInfo('李永乐',          '9458053'))
    uperList.append(UperInfo('巫师财经',        '472747194'))
    uperList.append(UperInfo('回形针PaperClip', '258150656'))
    uperList.append(UperInfo('柴知道',          '26798384',))
    uperList.append(UperInfo('吟游诗人基德',     '510856133',))
    saveRootPath = r'Y:\科普'
    # 并发数
    concurrency = 3

    MainProcess(uperList, saveRootPath, concurrency)