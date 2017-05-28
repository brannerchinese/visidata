from visidata import *

command('D', 'vd.push(vd.editlog)', 'push the editlog')

def open_vd(p):
    return EditLog(p.name, p)

class EditLog(Sheet):
    def __init__(self, name, *args):
        super().__init__(name, *args)

        self.columns = [
            ColumnItem('sheet_id', 0),
            ColumnItem('keystrokes', 1),
            ColumnItem('input', 2),
        ]

        self.command('a', 'sheet.replay(cursorRow); status("replayed one row")', 'replay this editlog')
        self.command('ga', 'sheet.replay()', 'replay this editlog')

        self.sheetmap = {}

    def append(self, sheetname, keystrokes, args=''):
        if sheetname == self.name:
            return

        self.rows.append([ sheetname, keystrokes, args ])

    def first_load(self, vs):
        self.append(vs.name, 'first_load', vs.visibleColNames)

    @async
    def reload(self):
        reload_tsv_sync(self)

        self.sheetmap = {}
        for sheetname, keystrokes, args in self.rows:
            if keystrokes == 'first_load':
                # use args to figure out which sheet maps to this sheetname
                for vs in vd().sheets:
                    if vs.visibleColNames == args:
                        if sheetname in self.sheetmap:
                            error('multiple sheets with same signature: %s' % args)

                        self.sheetmap[sheetname] = vs

    def replay_one(self, r):
        sheetname, keystrokes, args = r

        vd().current_replay_row = r
        if keystrokes != 'first_load':
            vs = self.sheetmap[sheetname]
            vs.exec_command(g_globals, vs.commands[keystrokes])
        vd().current_replay_row = None

    @async
    def replay(self):
        for r in self.rows:
            self.replay_one(r)
            while len(vd().unfinishedTasks) > 1:  # ours will be there always
                pass

        status('replayed entire %s' % self.name)

    def set_last_args(self, args):
        if vd().sheets[0] is not self:  # only set args if not on editlog (because editlog commands are not logged)
            self.rows[-1][2] = args

vd().editlog = EditLog('__editlog__')
vd().current_replay_row = None
