import subprocess
from os import write, close, remove
from os.path import basename, splitext, dirname
from tempfile import mkstemp
from json import dumps

from pipeline.compilers import SubProcessCompiler, CompilerError
from whatmatters import settings

from logging import getLogger
log = getLogger('development')

class RequireCompiler(SubProcessCompiler):

    output_extension = 'optimised.js'

    def match_file(self, filename):
        return filename.endswith('.js')

    def compile_file(self, infile, outfile, outdated=False, force=False):
        #log.debug('infile: %s' % infile)
        #log.debug('outfile: %s' % outfile)
        if not outdated and not force:
            #log.debug('not outdated and not forced')
            return # No need to recompile the file

        # Get the options for requirejs
        options = settings.PIPELINE_REQUIREJS_BUILD
        options['out'] = outfile

        # Make a temporary file
        fd, name = mkstemp()

        write(fd, '(%s)' % dumps(options))
        close(fd)

        # Execute the command
        command = "%s -o %s" % (settings.PIPELINE_REQUIREJS_BINARY, name)

        response = self.execute_command(command, cwd=settings.PROJECT_ROOT)
        remove(name)

        return response

    # We override this because the default package only puts stderr as the
    # message, yet r.js outputs everything to stdout  :(
    def execute_command(self, command, content=None, cwd=None):
        pipe = subprocess.Popen(command, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        if content:
            pipe.stdin.write(content)
            pipe.stdin.close()

        compressed_content = pipe.stdout.read()
        pipe.stdout.close()

        error = pipe.stderr.read()
        pipe.stderr.close()

        if pipe.wait() != 0:
            if not error:
                error = "Unable to apply %s compiler. Output was: \n%s"
                error = error % (self.__class__.__name__, compressed_content)
            raise CompilerError(error)

        if self.verbose:
            print error

        return compressed_content