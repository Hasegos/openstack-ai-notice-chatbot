-- ================================================
-- 울산과학대학교 학과 seed 데이터 (실제 학과 기준)
-- ================================================

INSERT INTO departments (school_id, dept_name, notice_url, is_active)
SELECT s.school_id, d.dept_name, d.notice_url, True
FROM (VALUES
  -- 공학계열
  ('울산과학대학교', '컴퓨터공학과', 'https://www.uc.ac.kr/computer/CMS/Board/Board.do?mCode=MN052'),
  ('울산과학대학교', '게임영상학과', 'https://www.uc.ac.kr/cdesign/CMS/Board/Board.do?mCode=MN034'),
  ('울산과학대학교', '건축과', 'https://www.uc.ac.kr/archi/CMS/Board/Board.do?mCode=MN017'),
  ('울산과학대학교', '실내건축디자인과', 'https://www.uc.ac.kr/iadesign/CMS/Board/Board.do?mCode=MN040'),
  ('울산과학대학교', '기계공학부', 'https://www.uc.ac.kr/me/CMS/Board/Board.do?mCode=MN071'),
  ('울산과학대학교', '전기전자공학부', 'https://www.uc.ac.kr/electric/CMS/Board/Board.do?mCode=MN057'),
  ('울산과학대학교', '화학공학과', 'https://www.uc.ac.kr/chemical/CMS/Board/Board.do?mCode=MN033'),
  ('울산과학대학교', '조선해양시스템공학과', 'https://www.uc.ac.kr/ship/CMS/Board/Board.do?mCode=MN032'),
  ('울산과학대학교', '융합안전공학과', 'https://www.uc.ac.kr/safety/CMS/Board/Board.do?mCode=MN034'),
  ('울산과학대학교', '반도체공학과', 'https://www.uc.ac.kr/semi/CMS/Board/Board.do?mCode=MN030'),
  
  -- 인문사회계열
  ('울산과학대학교', '사회복지학과', 'https://www.uc.ac.kr/family/CMS/Board/Board.do?mCode=MN036'),
  ('울산과학대학교', '유아교육과', 'https://www.uc.ac.kr/baby/CMS/Board/Board.do?mCode=MN042'),
  ('울산과학대학교', '세무회계학과', 'https://www.uc.ac.kr/account/CMS/Board/Board.do?mCode=MN033'),
  ('울산과학대학교', '글로벌비즈니스학과', 'https://www.uc.ac.kr/global/CMS/Board/Board.do?mCode=MN042'),
  ('울산과학대학교', '국제학부', 'https://www.uc.ac.kr/if/CMS/Board/Board.do?mCode=MN020'),
  
  
  -- 자연과학계열
  ('울산과학대학교', '간호학부', 'https://www.uc.ac.kr/nursing/CMS/Board/Board.do?mCode=MN079'),
  ('울산과학대학교', '물리치료학과', 'https://www.uc.ac.kr/physical/CMS/Board/Board.do?mCode=MN016'),
  ('울산과학대학교', '치위생학과', 'https://www.uc.ac.kr/dental/CMS/Board/Board.do?mCode=MN040'),
  ('울산과학대학교', '식품영양학과', 'https://www.uc.ac.kr/fn/CMS/Board/Board.do?mCode=MN041'),
  ('울산과학대학교', '호텔조리제빵과', 'https://www.uc.ac.kr/hotel/CMS/Board/Board.do?mCode=MN044'),
  ('울산과학대학교', '스포츠재활학부', 'https://www.uc.ac.kr/sports/CMS/Board/Board.do?mCode=MN039'),
  ('울산과학대학교', '반려동물보건과', 'https://www.uc.ac.kr/pet/CMS/Board/Board.do?mCode=MN020'),

  -- 성인학습자과정
  ('울산과학대학교', '스포츠건강재활학과' ,NULL),
  ('울산과학대학교', '사회복지상담학과', 'https://www.uc.ac.kr/family2/CMS/Board/Board.do?mCode=MN017'),
  ('울산과학대학교', '푸드케어학과', 'https://www.uc.ac.kr/fc/CMS/Board/Board.do?mCode=MN029'),
  ('울산과학대학교', '골프산업과', 'https://www.uc.ac.kr/golf/CMS/Board/Board.do?mCode=MN033'),
  ('울산과학대학교', '인테리어시공학과', 'https://www.uc.ac.kr/icdesign/CMS/Board/Board.do?mCode=MN027')
) AS d(school_name, dept_name, notice_url)
JOIN schools s ON s.school_name = d.school_name;