import os
import json
import time
import random
import argparse
from llm_client import call_chat

def read_txt(path):
    with open(path, "r", encoding="utf8") as f:
        return f.read()

def read_json(path):
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)

def write_json(path, data, indent=2):
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

class PlayerState:
    def __init__(self, save_file=""):
        self.save_file = save_file
        self.log = []
        self.known_students = {}
        self.attributes = {"energy": 10}
        self.ended = False

    def save(self):
        write_json(self.save_file, {
            "log": self.log,
            "known_students": self.known_students,
            "attributes": self.attributes,
            "ended": self.ended
        })

    def load(self):
        d = read_json(self.save_file)
        self.log = d["log"]
        self.known_students = d["known_students"]
        self.attributes = d["attributes"]
        self.ended = d["ended"]

class CampusGame:
    def __init__(self, config_file):
        cfg = read_json(config_file)
        self.model = cfg.get("model", "gpt-3.5-turbo")
        static_parts = cfg.get("static_dir", ["static"])
        self.static_dir = os.path.join(*static_parts)
        state_parts = cfg.get("state_dir", ["state"])
        self.state_dir = os.path.join(*state_parts)
        output_parts = cfg.get("output_dir", ["runs"])
        self.output_dir = os.path.join(*output_parts)

        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # load prompts
        self.prompts = {}
        user_prompt_dir = os.path.join(self.static_dir, "user_prompt")
        for fname in os.listdir(user_prompt_dir):
            key = fname[:-4]
            self.prompts[key] = read_txt(os.path.join(user_prompt_dir, fname))

        # load students
        self.students = {}
        students_dir = os.path.join(self.static_dir, "students")
        for fname in os.listdir(students_dir):
            if fname.endswith(".json"):
                sid = fname[:-5]
                self.students[sid] = read_json(os.path.join(students_dir, fname))

        self.state = PlayerState()
        self.save_file = ""

    def start(self):
        print(self.prompts["start"])
        choice = input().strip()
        if choice == "2":
            saves = [f for f in os.listdir(self.state_dir) if f.endswith(".json")]
            if not saves:
                print("沒有任何存檔，開始新遊戲。")
                self.new_game()
            else:
                print("現有存檔：")
                for i, s in enumerate(saves):
                    print(f"({i+1}) {s}")
                sel = input("選一個存檔編號或直接按 Enter 新遊戲：").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(saves):
                    self.save_file = os.path.join(self.state_dir, saves[int(sel)-1])
                    self.state = PlayerState(self.save_file)
                    self.state.load()
                    print("載入完成。")
                else:
                    self.new_game()
        else:
            self.new_game()

        self.loop()

    def new_game(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.save_file = os.path.join(self.state_dir, f"save_{ts}.json")
        self.state = PlayerState(self.save_file)
        self.state.log.append(self.prompts["opening"])
        self.state.save()

    def loop(self):
        while True:
            friends = [v['friendship'] for v in self.state.known_students.values()] if self.state.known_students else []
            if sum(1 for f in friends if f >= 12) >= 2 and not self.state.ended:
                self.end_sequence()
                break

            print("\n行動選單：")
            print("(1) 逛校園（隨機遇到同學）")
            print("(2) 查看同學名單 / 圖鑑")
            print("(3) 與認識的人互動")
            print("(4) 休息（回復體力）")
            print("(0) 存檔並離開")
            sel = input("選擇：").strip()
            if sel == "1":
                self.action_explore()
            elif sel == "2":
                self.action_show_pedia()
            elif sel == "3":
                if not self.state.known_students:
                    print("你還沒認識任何同學，先去逛校園遇見人吧。")
                else:
                    self.action_interact()
            elif sel == "4":
                self.state.attributes['energy'] = min(20, self.state.attributes['energy'] + 5)
                ev = "休息一下，體力 +5。"
                print(ev)
                self.state.log.append(ev)
                self.state.save()
            elif sel == "0":
                self.state.save()
                print("已存檔，離開遊戲。")
                break
            else:
                print("無效輸入。")

    def action_explore(self):
        candidates = list(self.students.keys())
        found = random.choice(candidates)
        s = self.students[found]
        text = f"你在學生餐廳遇到 {s['name']}（{s['major']}）。簡介：{s['bio']}"
        print(text)
        self.state.log.append(text)

        if found not in self.state.known_students:
            self.state.known_students[found] = {
                'info': s,
                'friendship': 0
            }
            add = f"你認識了 {s['name']}，已加入校園名錄。"
            print(add)
            self.state.log.append(add)
        self.state.save()

    def action_show_pedia(self):
        if not self.state.known_students:
            print("名錄空空如也。")
            return
        print("你認識的人：")
        for i,(sid,entry) in enumerate(self.state.known_students.items(), start=1):
            print(f"({i}) {entry['info']['name']} - 友誼度：{entry['friendship']}")
        input("按 Enter 繼續…")

    def action_interact(self):
        keys = list(self.state.known_students.keys())
        for i,k in enumerate(keys, start=1):
            print(f"({i}) {self.state.known_students[k]['info']['name']}")
        sel = input("選擇要互動的對象編號：").strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(keys)):
            print("無效選擇。")
            return
        sid = keys[int(sel)-1]
        student = self.state.known_students[sid]['info']

        print("(1) 聊天 (2) 請教專業 (3) 邀約參加社團)")
        act = input("選擇互動方式：").strip()
        if act not in ('1','2','3'):
            print("無效輸入")
            return

        if act == '1':
            prompt = f"你是遊戲 NPC，扮演 {student['name']}（{student['major']}）。玩家想跟你聊天，談論 {', '.join(student['topics'])}。請寫一段 2-4 句的自然回應，並最後給出一句可以讓友誼度上升的建議（短句）。"
            resp = call_chat(self.model, [{'role':'user','content':prompt}], max_tokens=200)
            print("\n" + resp + "\n")
            self.state.log.append(f"與 {student['name']} 聊天：{resp}")
            inc = 3 if any(word in resp for word in ['一起','建議','可以']) else 1
            self.state.known_students[sid]['friendship'] += inc
            self.state.save()
        elif act == '2':
            q = input("你想問的問題（至少 5 字）：").strip()
            if len(q) < 5:
                print("問題太短。")
                return
            prompt = f"你是{student['name']}（{student['major']}），請用簡短清楚的方式回答學生的問題：\"{q}\"。回答 2-4 句，最後用一行評價：回答是否令人滿意（是/否）。"
            resp = call_chat(self.model, [{'role':'user','content':prompt}], max_tokens=250)
            print("\n" + resp + "\n")
            self.state.log.append(f"向 {student['name']} 請教：{q} 回覆：{resp}")
            if any(word in resp for word in ['是','滿意','令人滿意']):
                self.state.known_students[sid]['friendship'] += 4
            else:
                self.state.known_students[sid]['friendship'] += 0
            self.state.save()
        else:
            club = input("你想邀請對方參加哪個社團或活動（至少 2 字）：").strip()
            if len(club) < 2:
                print("輸入太短。")
                return
            prompt = f"你是{student['name']}。有人邀你加入「{club}」活動。請寫出 1) 你接受或拒絕的理由（1 兩句） 2) 一句可以讓關係更近的回應。"
            resp = call_chat(self.model, [{'role':'user','content':prompt}], max_tokens=200)
            print("\n" + resp + "\n")
            self.state.log.append(f"邀約 {student['name']} 參加 {club}：{resp}")
            if any(word in resp for word in ['接受','想試試','好啊','可以']):
                self.state.known_students[sid]['friendship'] += 5
            else:
                self.state.known_students[sid]['friendship'] += 1
            self.state.save()

    def end_sequence(self):
        history = "\n".join(self.state.log[-80:])
        prompt_template = self.prompts['review_prompt']
        prompt = prompt_template.replace('{history}', history)
        resp = call_chat(self.model, [{'role':'user','content':prompt}], max_tokens=400)
        try:
            review = json.loads(resp)
        except Exception:
            review = {'comment': resp, 'score': 0, 'highlight': '', 'replay_tips': []}

        output = {
            'timestamp': time.strftime('%Y%m%d_%H%M%S'),
            'state': {
                'known_students': self.state.known_students,
                'attributes': self.state.attributes
            },
            'history': self.state.log,
            'review': review
        }
        out_file = os.path.join(self.output_dir, f"run_{output['timestamp']}.json")
        write_json(out_file, output)
        print("\n=== 學期回顧 ===")
        print(json.dumps(review, ensure_ascii=False, indent=2))
        print(f"\n遊戲紀錄已儲存：{out_file}")
        self.state.ended = True
        self.state.save()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='lab2_config.json')
    args = parser.parse_args()

    apikey = input('請輸入 OpenAI API Key（或直接按 Enter 使用離線模擬模式）： ').strip()
    if apikey:
        os.environ['OPENAI_API_KEY'] = apikey

    game = CampusGame(args.config)
    game.start()

if __name__ == '__main__':
    main()
